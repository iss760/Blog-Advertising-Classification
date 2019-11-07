import pickle
import json
import time

from collections import OrderedDict
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

# 데이터 베이스 접근을 위한 모듈
from db_connect import DB

# 토크나이징을 위한 모듈
from tokenizer import KrTokenizer


# 블로그 카테고리 분류 모델 (나이브 베이즈)
class BCC_NB:
    def __init__(self):
        self.db = DB()
        self.krt = KrTokenizer()
        self.dtmvector = CountVectorizer()
        self.tfidf_transformer = TfidfTransformer()
        self.tfidf = TfidfVectorizer()
        self.category_list = {
                                100: '영화, 문화',
                                101: '육아, 결혼',
                                102: '상품리뷰',
                                103: '여행',
                                104: '맛집, 음식',
                                105: 'IT, 인터넷',
                                106: '사회, 정치',
                                107: '비즈니스, 경제',
                                108: '패션, 미용'
                            }

    # 토크나이징, 전처리 함수
    def tokenize(self, corpus, use_mecab=True):
        """
        :param corpus: (str) 블로그 하나의 문서
        :param use_mecab: (bool) mecab 사용 여부, default=True
        :return: (list) 토크나이징 된 블로그 문서
        """
        if use_mecab is True:
            token_doc = self.krt.extract_morphs_for_single_doc(corpus, True)
        else:
            token_doc = self.krt.extract_morphs_for_single_doc(corpus, False)
        return token_doc

    # 토크나이징 된 문서를 하나의 문서로 변환 (모델 적용을 위해)
    def token_to_corpus(self, token_doc):
        """
        :param token_doc: (list)  토크나이징으로 리스트화 된 하나의 문서
        :return: (str) 토크나이징이 완료된 하나의 문서
        """
        result = ''
        for token in token_doc:
            result = result + ' ' + str(token)
        return result

    # 모델 저장 함수
    def model_save(self, model):
        f = open('classifier_nb.pickle', 'wb')
        pickle.dump(model, f)
        f.close()

    # 모델 로드 함수
    def model_load(self):
        f = open('classifier_nb.pickle', 'rb')
        model = pickle.load(f)
        f.close()

        return model

    # 모델 학습 함수
    def model_train(self):
        # 학습 데이터 로드
        sql = 'SELECT body, category_num FROM blog_category_classification.posting order by rand()'
        pre_data = self.db.data_load(sql)

        # 학습 데이터 토크나이징, 전처리
        af_data = []
        for _data in pre_data:
            temp = []
            body = self.token_to_corpus(self.tokenize(_data[0], True))
            category_num = _data[1]
            temp.append(body)
            temp.append(category_num)
            af_data.append(temp)

        X_train = []
        y_train = []
        for _data in af_data:
            X_train.append(_data[0])
            y_train.append(_data[1])

        print('train data_set size : ' + str(len(X_train)))

        # 학습 데이터를 DTM, TF-IDF 행렬로 변환
        X_train_dtm = self.dtmvector.fit_transform(X_train)
        X_train_tfidfv = self.tfidf_transformer.fit_transform(X_train_dtm)
        X_train_tfidf = self.tfidf.fit(X_train)
        print(X_train_dtm.shape)

        # TF-IDF 토큰 저장
        temp = []
        for key in X_train_tfidf.vocabulary_.keys():
            temp.append(key)
        save_data = OrderedDict()
        save_data['token'] = temp
        save_data['doc_count'] = len(af_data)
        json.dump(save_data, open('./naive_bayes_tf_idf.json', 'w', encoding='utf-8'),
                  ensure_ascii=False, indent='\t')

        # 모델 학습
        mod = MultinomialNB()
        mod.fit(X_train_tfidfv, y_train)

        # 모델 저장
        self.model_save(mod)

    # 모델 테스트 함수 (학습 차원 내에서의 범위 한정)
    def model_test(self):
        # 모델 로드
        mod = self.model_load()

        # TF-IDF 토큰 로드
        with open('./naive_bayes_tf_idf.json', 'r', encoding='UTF-8') as f:
            load_data = json.load(f)
        token_ls = load_data['token']

        # 테스트 데이터 로드
        sql = 'SELECT body, category_num FROM blog_category_classification.posting order by rand() limit 100'
        pre_data = self.db.data_load(sql)

        # 학습 데이터 토크나이징, 전처리
        af_data = []
        for _data in pre_data:
            temp = []
            body = self.token_to_corpus(self.tokenize(_data[0], True))
            category_num = _data[1]
            temp.append(body)
            temp.append(category_num)
            af_data.append(temp)

        X_temp = []
        y_test = []
        for _data in af_data:
            X_temp.append(_data[0])
            y_test.append(_data[1])

        X_test = X_temp
        X_fit_dim = ''
        for token in token_ls:
            X_fit_dim = X_fit_dim + ' ' + str(token)
        X_test.insert(0, X_fit_dim)
        y_test.insert(0, 0)

        print('test data_set size : ', len(X_test) - 1)

        MultinomialNB(alpha=1.0, class_prior=None, fit_prior=True)

        # 테스트 데이터를 DTM, TF-IDF 행렬로 변환
        X_test_dtm = self.dtmvector.fit_transform(X_test)
        X_test_tfidf = self.tfidf_transformer.fit_transform(X_test_dtm)
        print(X_test_tfidf.shape)

        # 테스트 데이터에 대한 예측
        predicted = mod.predict(X_test_tfidf)

        # 예측값과 실제값 비교
        print("정확도:", accuracy_score(y_test[1:], predicted[1:]))

    # 모델 평가 함수
    def model_evaluation(self):
        # 학습 데이터 로드
        sql = 'SELECT body, category_num FROM blog_category_classification.posting order by rand()'
        pre_data = self.db.data_load(sql)

        # 학습 데이터 토크나이징, 전처리
        af_data = []
        for _data in pre_data:
            temp = []
            body = self.tokenize(_data[0], True)
            category_num = _data[1]
            temp.append(body)
            temp.append(category_num)
            af_data.append(temp)

        X = []
        y = []
        for _data in af_data:
            X.append(_data[0])
            y.append(_data[1])

        # 학습, 테스트 데이터 분할 (test_data=0.2)
        sym = int(len(af_data) * 0.8)
        X_train = X[:sym]
        X_test = X[sym:]
        y_train = y[:sym]
        y_test = y[sym:]

        print('train data_set size : ' + str(len(X_train)))
        print('test data_set size : ' + str(len(X_test)))

        # 학습 데이터를 DTM, TF-IDF 행렬로 변환
        X_train_dtm = self.dtmvector.fit_transform(X_train)
        X_train_tfidfv = self.tfidf_transformer.fit_transform(X_train_dtm)
        print(X_train_dtm.shape)

        # 모델 학습
        mod = MultinomialNB()
        mod.fit(X_train_tfidfv, y_train)

        MultinomialNB(alpha=1.0, class_prior=None, fit_prior=True)

        # 테스트 데이터를 DTM, TF-IDF 행렬로 변환
        X_test_dtm = self.dtmvector.transform(X_test)
        X_test_tfidf = self.tfidf_transformer.transform(X_test_dtm)

        # 테스트 데이터에 대한 예측
        predicted = mod.predict(X_test_tfidf)

        # 예측값과 실제값 비교
        print("정확도:", round(accuracy_score(y_test, predicted), 3))

    # 카테고리 분류 함수
    def classifier(self, data, use_save_model=False, use_mecab=True):
        """
        :param data: (list or str) 분류 하고자 하는 하나 또는 복수개의 블로그 문서
        :return: None
        """
        t_tokenizing_s = time.time()    # 토크나이징 시작 시간

        # 분류할 데이터 토크나이징
        if use_mecab is True:
            token_doc_ls = []
            for _data in data:
                token_doc = self.tokenize(_data, use_mecab=True)
                token_doc_ls.append(token_doc)
        else:
            token_doc_ls = []
            for _data in data:
                token_doc = self.tokenize(_data, use_mecab=False)
                token_doc_ls.append(token_doc)

        t_tokenizing = time.time() - t_tokenizing_s     # 토크나이징 끝 시간

        # 세이브 모델 사용
        if use_save_model is True:
            # 모델 로드
            mod = self.model_load()

            # TF-IDF 토큰 로드
            with open('./naive_bayes_tf_idf.json', 'r', encoding='UTF-8') as f:
                load_data = json.load(f)
            token_ls = load_data['token']

            t_padding_s = time.time()       # 패딩 작업 시작 시간

            # 분류 할 데이터와 TF-IDF 토큰 결합 (차원 수를 맞추기 위한 패딩 작업)
            X_predict = []
            for token_doc in token_doc_ls:
                temp = []
                for token in token_doc:
                    if token in token_ls:
                        temp.append(token)
                X_predict.append(self.token_to_corpus(temp))
            X_fit_dim = ''
            for token in token_ls:
                X_fit_dim = X_fit_dim + ' ' + str(token)
            X_predict.insert(0, X_fit_dim)

            t_padding = time.time() - t_padding_s       # 패딩 작업 끝 시간

            MultinomialNB(alpha=1.0, class_prior=None, fit_prior=True)

            # 학습 데이터를 DTM, TF-IDF 행렬로 변환
            X_predict_dtm = self.dtmvector.fit_transform(X_predict)
            X_predict_tfidf = self.tfidf_transformer.fit_transform(X_predict_dtm)
            # print(X_predict_tfidf.shape)

            predicted = mod.predict(X_predict_tfidf)

            # 결과 출력
            for i, _predicted in enumerate(predicted[1:]):
                print(i, ')    ', _predicted, ': ', self.category_list[int(_predicted)])

            # 시간 출력
            print('\n')
            print('tokenizing time : ', round(t_tokenizing, 2))
            print('padding time : ', round(t_padding, 2))

        # 세이브 모델 미사용
        else:
            size = len(data)

            # 학습 데이터 로드
            sql = 'SELECT body, category_num FROM blog_category_classification.posting order by rand()'
            pre_data = self.db.data_load(sql)

            # 학습 데이터 토크나이징, 전처리
            af_data = []
            for _data in pre_data:
                temp = []
                body = self.token_to_corpus(self.tokenize(_data[0], True))
                category_num = _data[1]
                temp.append(body)
                temp.append(category_num)
                af_data.append(temp)

            df_doc_ls = []
            for token_doc in token_doc_ls:
                temp = []
                temp.append(self.token_to_corpus(token_doc))
                temp.append('')
                df_doc_ls.append(temp)

            # 학습 데이터, 분류할 데이터 정리
            X = []
            y = []
            af_data = af_data + df_doc_ls
            for i, _data in enumerate(af_data):
                X.append(_data[0])
                y.append(_data[1])
            sym = int(len(X) - size)
            X_train = X[:sym]
            X_predict = X[sym:]
            y_train = y[:sym]

            for i in X_predict:
                print(i)

            print('train data_set size : ', len(X_train))
            print('predict data_set size : ', len(X_predict))

            # 학습 데이터를 DTM, TF-IDF 행렬로 변환
            X_train_dtm = self.dtmvector.fit_transform(X_train)
            tfidfv = self.tfidf_transformer.fit_transform(X_train_dtm)
            print(X_train_dtm.shape)

            # 모델 학습
            mod = MultinomialNB()
            mod.fit(tfidfv, y_train)

            MultinomialNB(alpha=1.0, class_prior=None, fit_prior=True)

            # 분류 할 데이터를 DTM, TF-IDF 행렬로 변환
            X_test_dtm = self.dtmvector.transform(X_predict)
            X_test_tfidf = self.tfidf_transformer.transform(X_test_dtm)

            # 분류
            prediction = mod.predict(X_test_tfidf)  # 테스트 데이터에 대한 예측

            # 결과 출력
            for i, _prediction in enumerate(prediction):
                print(i, ')    ', _prediction, ': ', self.category_list[int(_prediction)])

            if len(prediction) == 1:
                return int(prediction)
            else:
                return prediction
