import pickle
import os
import numpy as np
from konlpy.tag import Okt

import torch
from torch.autograd import Variable
import torch.nn.functional as F

from keras.preprocessing.sequence import pad_sequences

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class Sentiment_Analysis:
    def __init__(self):
        self.okt = Okt()

        # 모델, 토큰 저장 위치
        self.pytorch_model_path = './LSTM_model.pickle'
        self.keras_model_path = './LSTM_model2.pickle'
        self.pytorch_token_path = './LSTM_model_token.pickle'
        self.keras_token_path = './LSTM_model2_token.pickle'

        # 불용어 리스트
        self.stopwords = ['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']

        # 학습 모델의 샘플당 최대(설정) 길이
        self.max_len = 30

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

    # pytorch 모델 분류 함수
    def analysis_pytorch(self, data):
        model = self.load_pickle(self.pytorch_model_path)
        idx2token = self.load_pickle(self.pytorch_token_path)
        token2idx = {val: key for key, val in idx2token.items()}

        # 데이터 전처리
        idx_data, tokens_ls = self.tokenizing(data)

        # 정수 인코딩
        x_input = []
        seq_len = []
        for tokens in tokens_ls:
            temp = [token2idx[token] for token in tokens if token in list(token2idx.keys())]

            # padding
            # 입력 데이터 길이 조정 (최대 길이보다 길 경우 최대 길이까지만 사용)
            if len(temp) >= self.max_len:
                temp = temp[:self.max_len]
                seq_len.append(len(temp))
            # 최대 길이보다 짧을 경우 <PAD>
            else:
                seq_len.append(len(temp))
                temp = temp + [0] * (self.max_len - len(temp))

            x_input.append(temp)

        # sequence 순서대로 정렬
        sorted_idx = np.argsort(np.array(seq_len))[::-1]
        x_input = Variable(torch.LongTensor(np.array(x_input)[sorted_idx]))
        seq_len = Variable(torch.LongTensor(np.array(seq_len)[sorted_idx]))
        idx_data = Variable(torch.LongTensor(np.array(idx_data)[sorted_idx]))

        # 예측
        scores = model(x_input, seq_len)
        predict = F.softmax(scores, dim=1).argmax(dim=1)

        # 예측값 재정렬
        prediction = {}
        for idx, _predict in zip(idx_data, predict):
            prediction[int(idx)] = int(_predict)
        prediction = sorted(prediction.items())

        # 예측값 출력
        for _prediction in prediction:
            _prediction = list(_prediction)
            if _prediction[1] == 1:
                print(_prediction[0] + 1, ')', '긍정')
            else:
                print(_prediction[0] + 1, ')', '부정')

    # Keras 모델 분류 함수
    def analysis_keras(self, data):
        """
        :param data: (list, str) 예측 하고자 하는 하나 혹은 복수개의 리뷰
        :return: None
        """
        # 모델, 토큰 로드
        model = self.load_pickle(self.keras_model_path)
        idx2token = self.load_pickle(self.keras_token_path)
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

            x_input.append(temp)

        # padding
        x_input = pad_sequences(x_input, maxlen=self.max_len)

        # 예측
        prediction = model.predict_classes(x_input, batch_size=32)

        # 예측값 출력
        for idx, _prediction in zip(idx_data, prediction):
            if _prediction[0] == 1:
                print(idx + 1, ')', '긍정')
            else:
                print(idx + 1, ')', '부정')
