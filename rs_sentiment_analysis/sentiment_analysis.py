import pickle
import os
from konlpy.tag import Okt

from keras.preprocessing.sequence import pad_sequences

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class Sentiment_Analysis:
    def __init__(self):
        self.okt = Okt()

        # 모델, 토큰 저장 위치
        self.model_path = './rs_LSTM_model.pickle'
        self.token_path = './rs_LSTM_model_token.pickle'

        # 불용어 리스트
        self.stopwords = ['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']

        # 학습 모델의 샘플당 최대(설정) 길이
        self.max_len = 200

        # 모델이 학습 된 최대 단어 개수
        self.n_max_word = 30000

    # pickle 문서 로드 함수
    def load_pickle(self, file_path):
        f = open(file_path, 'rb')
        model = pickle.load(f)
        f.close()
        return model

    # 토크나이징, 불용어 제거 함수
    def tokenizing(self, data):
        tokens_ls = []
        idx_data = []
        for idx, sentence in enumerate(data):
            # 토크나이징
            temp_x = self.okt.morphs(sentence, stem=True)
            # 불용어 제거
            temp_x = [word for word in temp_x if word not in self.stopwords]
            # 공백 데이터 제거
            if len(temp_x) != 0:
                tokens_ls.append(temp_x)
                idx_data.append(idx)

        return idx_data, tokens_ls

    #  감성 분류 함수
    def sentiment_analysis(self, data):
        """
        :param data: (list, str) 예측 하고자 하는 하나 혹은 복수개의 리뷰
        :return: None
        """
        # 모델, 토큰 로드
        model = self.load_pickle(self.model_path)
        idx2token = self.load_pickle(self.token_path)
        token2idx = {val: key for key, val in idx2token.items()}

        # 데이터 전처리
        idx_data, tokens_ls = self.tokenizing(data)

        # 정수 인코딩
        x_input = []
        for tokens in tokens_ls:
            temp = [token2idx[token] for token in tokens if token in list(token2idx.keys())]

            # 입력 데이터 길이 조정 (최대 길이보다 길 경우 최대 길이까지만 사용)
            if len(temp) >= self.max_len:
                temp = temp[:self.max_len]

            # 입력 데이터 중 최대 단어를 벗어나는 단어 삭제
            temp2 = [_temp for _temp in temp if _temp < self.n_max_word]

            x_input.append(temp2)

        # padding
        x_input = pad_sequences(x_input, maxlen=self.max_len)

        # 예측
        prediction = model.predict(x_input, batch_size=32)

        # 예측값 출력
        for idx, _prediction in zip(idx_data, prediction):
            if _prediction[0] > 0.5:
                print(idx + 1, ')', '긍정')
                return 1
            else:
                print(idx + 1, ')', '부정')
                return 0
