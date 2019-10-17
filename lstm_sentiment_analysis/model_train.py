import pickle
import pandas as pd
import numpy as np

import torch.nn as nn
import torch
from torch.autograd import Variable
import torch.nn.functional as F
import random

from konlpy.tag import Okt
try:
    from konlpy.tag import Mecab
    from eunjeon import Mecab
except Exception as e:
    print(e)
    import MeCab

from collections import defaultdict

from lstm_sentiment_analysis.model import Sentiment_Analysis_LSTM

okt = Okt()
mecab = Mecab()


# 모델 저장 함수
def save_model(model, file_name='LSTM_model'):
    f = open(file_name + '.pickle', 'wb')
    pickle.dump(model, f)
    f.close()


# 모델 로드 함수
def load_model(file_name='LSTM_model'):
    f = open(file_name + '.pickle', 'rb')
    model = pickle.load(f)
    f.close()
    return model


# 데이터 로드 함수
def load_data(file_path):
    data = pd.read_table(file_path)
    return data


# 전처리 함수
def pre_processing(data, use_mecab=False):
    """
    :param data: (list) 하나 또는 복수개의 문서(리뷰) 데이터
    :param use_mecab: (bool) mecab 사용 여부
    :return: x: (list) [[token, token, ... ], [token, ...]] 형식의 data set
              y: (list) data set 의 라벨링 리스트
    """
    # 공백 데이터 제거
    data = data.dropna(how='any')

    # 전처리, 데이터 분할
    x = []
    y = []
    # data['document'] = data['document'].str.replace("[^ㄱ-ㅎㅏ-ㅣ가-힣 ]", "")
    stopwords = ['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']
    for sentence, label in zip(data['document'], data['label']):
        # 토크나이징
        if use_mecab is True:
            temp_x = [x for x in mecab.morphs(sentence) if len(x) > 1]
        else:
            temp_x = okt.morphs(sentence, stem=True)
        # 불용어 제거
        temp_x = [word for word in temp_x if word not in stopwords]
        # 공백 데이터 제거
        if len(temp_x) == 0:
            continue
        x.append(temp_x)
        y.append(label)

    return x, y

# padding 함수 (max_length 의 길이 만큼 <PAD> 추가)
def add_padding(data, max_length):
    """
    :param data: (list) 토크나이징 된 하나 혹은 복수개의 문서(리뷰)
    :param max_length: (int) 한 문장의 최대(설정) 길이
    :return: data: (list) padding  처리 된 데이터
              seq_length_ls: (list) <PAD>를 제외한 유니크 토큰의 갯수
    """
    pad = '<PAD>'
    seq_length_ls = []

    for i, tokens in enumerate(data):
        seq_length = len(tokens)

        # 짧으면 <PAD> 추가
        if seq_length < max_length:
            seq_length_ls.append(seq_length)
            data[i] += [pad] * (max_length - seq_length)

        # 길이가 길면, max_length 까지의 token 만 사용
        elif seq_length >= max_length:
            seq_length_ls.append(max_length)
            data[i] = tokens[:max_length]

    return data, seq_length_ls


# 정수 인코딩 함수
def integer_encoding(data):
    for tokens in data:
        yield [token2idx[token] for token in tokens]
    return


# sequence 순서대로 정렬해주는 함수
def sort_for_packing(x, y, seq_len):
    sorted_idx = np.argsort(np.array(seq_len))[::-1]

    x = Variable(torch.LongTensor(np.array(x)[sorted_idx]))
    y = Variable(torch.LongTensor(np.array(y)[sorted_idx]))
    seq_len = Variable(torch.LongTensor(np.array(seq_len)[sorted_idx]))

    return x, y, seq_len


# learning_rate 조정 함수
def adjust_learning_rate(optimizer, epoch, init_lr=0.001, lr_decay_epoch=10):
    """
    :param optimizer: (optimizer) 옵티마이저
    :param epoch: (int) epoch
    :param init_lr: (float) 최초
    :param lr_decay_epoch: (int) 학습 속도가 감소하는 epoch 주기
    :return: (optimizer) 옵티마이저
    """
    # lr_decay_epoch epoch 마다 0.1 배씩 학습 속도 감소
    lr = init_lr * (0.1**(epoch // lr_decay_epoch))

    if epoch % lr_decay_epoch == 0:
        print('LR is set to %s' %(lr))

    for param_group in optimizer.param_groups:
        param_group['lr'] = lr

    return optimizer

# 데이터 로드
train_data_path = './ratings_train.txt'
test_data_path = './ratings_test.txt'
train_data = load_data(train_data_path)
test_data = load_data(test_data_path)

# 데이터 전처리
x_train, y_train = pre_processing(train_data, False)
x_test, y_test = pre_processing(test_data)

# padding
max_length = 30
x_train, x_train_seq_length = add_padding(x_train, max_length)
x_test, x_test_seq_length = add_padding(x_test, max_length)

# 정수 인코딩
token2idx = defaultdict(lambda: len(token2idx))
pad = token2idx['<PAD>']
x_train = list(integer_encoding(x_train))
x_test = list(integer_encoding(x_test))

# 토큰 리스트 저장 (idx2token)
idx2token = {val: key for key, val in token2idx.items()}
f = open('LSTM_model_token.pickle', 'wb')
pickle.dump(idx2token, f)
f.close()

# sequence 순서대로 정렬
x_train, y_train, x_train_seq_length = sort_for_packing(x_train, y_train, x_train_seq_length)
x_test, y_test, x_test_seq_length = sort_for_packing(x_test, y_test, x_test_seq_length)

# 모델 로드
params = {
    'token2idx': token2idx,
    'max_sequence': 30,
    'vocab_size': len(token2idx),
    'embed_size': 100,
    'hid_size': 128,
    'n_layers': 2,
    'dropout': 0.5,
    'bidirectional': True,
    'n_category': 2,
}
model = Sentiment_Analysis_LSTM(**params)

# 모델 설정
epochs = 4
lr = 0.01
batch_size = 10000

# 옵티마이저, 손실 함수 설정
optimizer = torch.optim.Adam(model.parameters(), lr)
criterion = nn.CrossEntropyLoss(reduction='sum')

loss_ls = []
train_idx = np.arange(x_train.size(0))
test_idx = np.arange(x_test.size(0))

# epochs size 만큼 모델 학습
for epoch in range(1, epochs + 1):
    # 모델 학습 실시
    model.train()

    # input 데이터 순서 섞기
    random.shuffle(train_idx)
    x_train, y_train = x_train[train_idx], y_train[train_idx]
    x_train_seq_length = x_train_seq_length[train_idx]

    train_loss = 0

    # batch_size 만큼 학습
    for start_idx, end_idx in zip(range(0, x_train.size(0), batch_size),
                                  range(batch_size, x_train.size(0) + 1, batch_size)):
        # batch 뽑기
        x_batch = x_train[start_idx: end_idx]
        y_batch = y_train[start_idx: end_idx].long()
        x_batch_seq_length = x_train_seq_length[start_idx: end_idx]

        # sequence 순서대로 정렬
        x_batch, y_batch, x_batch_seq_length = sort_for_packing(x_batch, y_batch, x_batch_seq_length)

        # 예측 결과값
        scores = model(x_batch, x_batch_seq_length)
        predict = F.softmax(scores, dim=1).argmax(dim=1)

        # 정확도 계산
        acc = (predict == y_batch).sum().item() / batch_size

        # 손실율 계산
        loss = criterion(scores, y_batch)
        train_loss += loss.item()

        # backward, 다음 단계 진행
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 학습 상황 출력
        print('Train epoch : %s,  loss : %s,  accuracy :%.3f' % (epoch, train_loss / batch_size, acc))

        # 손실율 저장
        loss_ls.append(train_loss)

        # learning_rate 조정
        optimizer = adjust_learning_rate(optimizer, epoch, lr, 10)  # adjust learning_rate while training

# 모델 평가
model.eval()
scores = model(x_test, x_test_seq_length)
predict = F.softmax(scores, dim=1).argmax(dim=1)
acc = (predict == y_test.long()).sum().item() / y_test.size(0)
loss = criterion(scores, y_test.long())

# 평가 결과 출력
print('*************************************************************************************************')
print('*************************************************************************************************')
print('Test Loss : %.03f , Test Accuracy : %.03f' % (loss.item() / y_test.size(0), acc))
print('*************************************************************************************************')
print('*************************************************************************************************')

# 모델 저장
save_model(model)
