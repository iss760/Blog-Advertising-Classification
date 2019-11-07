import json
from numpy.linalg import norm
from numpy import dot
from nltk import FreqDist

from tokenizer import KrTokenizer

class BCC:
    def __init__(self):
        self.krt = KrTokenizer()

        self.category_list = {
            100: '맛집',
            101: '화장품/패션',
            102: 'IT/인터넷',
            103: '금융/제테크',
            104: '미디어/문화',
            105: '여행/숙박',
            106: '육아/출산',
            107: 'UNK'
        }

    # 코사인 유사도 측정 함수
    def cos_sim(self, doc1, doc2):
        """
        :param doc1: (list) 토크나이징, 정수 인코딩, BOW 된 문서
        :param doc2: (list) 토크나이징, 정수 인코딩, BOW 된 문서
        :return: (float) 두 문서의 코사인 유사도
        """
        return dot(doc1, doc2) / (norm(doc1) * norm(doc2))

    # 하나의 문서를 BOW(Bag of Word) 형태의 리스트로 변한 하는 함수
    def to_bow(self, token_list, rank_count=100, custom=False):
        """
        :param token_list: (list) 토크나이징 된 문서
        :param rank_count: (int) DTM 생성을 위한 카테고리 별 랭킹 토큰의 갯수, default=100
        :param custom: (bool) custom DTM 사용 유무
        :return: (list) 표준에 맞게 BOW 형식으로 변환 된 리스트
        """
        if custom is True:
            with open('./custom_dtm.json', 'r', encoding='UTF-8') as f:
                load_file = json.load(f)
            custom_token_list = load_file['token']
            size = len(load_file['token'])

            bow_list = [0 for _ in range(size)]
            for i, cs_token in enumerate(custom_token_list):
                for token in token_list:
                    if cs_token == token:
                        bow_list[i] = bow_list[i] + 1

        else:
            with open('./standard_dtm.json', 'r', encoding='UTF-8') as f:
                load_file = json.load(f)
            standard_token_list = load_file['token']
            size = len(load_file['token'])

            fdist = FreqDist(token_list)
            temp_list = fdist.most_common(rank_count)

            bow_list = [0 for _ in range(size)]
            for i, st_token in enumerate(standard_token_list):
                for token in temp_list:
                    if st_token == token[0]:
                        bow_list[i] = token[1]

        return bow_list

    # DTM 이용 classification
    def classifier_dtm(self, doc, custom=False):
        """
        :param doc: (list) 토크나이징, 정수 인코딩, BOW 된 문서
        :param custom: (bool) custom DTM 사용 유무
        :return: None
        """
        # 토크나이징
        tokenized_doc = self.krt.extract_morphs_for_single_doc(doc, use_mecab=False)

        # custom DTM 사용
        if custom is True:
            data = self.to_bow(tokenized_doc, custom=True)
            with open('./custom_dtm.json', 'r', encoding='UTF-8') as f:
                load_data = json.load(f)
            custom_dtm_value = load_data['dtm']
            category_size = len(custom_dtm_value)

            temp = []
            for i in range(category_size):
                temp.append(round(self.cos_sim(custom_dtm_value[i], data) * 100, 2))
        # standard DTM 사용
        else:
            data = self.to_bow(tokenized_doc, custom=False)
            with open('./standard_dtm.json', 'r', encoding='UTF-8') as f:
                load_data = json.load(f)
            standard_dtm_value = load_data['dtm']
            category_size = len(standard_dtm_value)

            temp = []
            for i in range(category_size):
                temp.append(round(self.cos_sim(standard_dtm_value[i], data) * 100, 2))

        temp_sorted = sorted(temp)
        temp_sorted.sort(reverse=True)
        first_category = self.category_list[int(temp.index(temp_sorted[0])) + 100]
        second_category = self.category_list[int(temp.index(temp_sorted[1])) + 100]
        if temp_sorted[0] < 50:
            print('UNK')
        else:
            print('1st : ' + str(first_category) + ' (' + str(temp_sorted[0]) + '%)')
            print('2nd : ' + str(second_category) + ' (' + str(temp_sorted[1]) + '%)')

    # TF-IDF 이용 classification
    def classifier_tf_idf(self, doc, custom=False):
        """
        :param doc: (list) 토크나이징, 정수 인코딩, BOW 된 문서
        :param custom: (bool) custom DTM 사용 유무
        :return: None
        """
        # 토크나이징
        tokenized_doc = self.krt.extract_morphs_for_single_doc(doc, use_mecab=False)

        # custom TF-IDF 사용
        if custom is True:
            data = self.to_bow(tokenized_doc, custom=True)
            with open('./custom_tf_idf.json', 'r', encoding='UTF-8') as f:
                load_data = json.load(f)
            custom_tf_idf_value = load_data['tf_idf']
            category_size = len(custom_tf_idf_value)

            temp = []
            for i in range(category_size):
                temp.append(round(self.cos_sim(custom_tf_idf_value[i], data) * 100, 2))
        # standard TF-IDF 사용
        else:
            data = self.to_bow(tokenized_doc, False)
            with open('./standard_tf_idf.json', 'r', encoding='UTF-8') as f:
                load_data = json.load(f)
            standard_tf_idf_value = load_data['tf_idf']
            category_size = len(standard_tf_idf_value)

            temp = []
            for i in range(category_size):
                temp.append(round(self.cos_sim(standard_tf_idf_value[i], data) * 100, 2))

        temp_sorted = sorted(temp)
        temp_sorted.sort(reverse=True)
        first_category = self.category_list[int(temp.index(temp_sorted[0])) + 100]
        second_category = self.category_list[int(temp.index(temp_sorted[1])) + 100]
        if temp_sorted[0] < 50:
            print('UNK')
        else:
            print('1st : ' + str(first_category) + ' (' + str(temp_sorted[0]) + '%)')
            print('2nd : ' + str(second_category) + ' (' + str(temp_sorted[1]) + '%)')
