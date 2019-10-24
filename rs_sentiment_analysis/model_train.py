import pickle
import pandas as pd
import random
from sklearn.model_selection import train_test_split
import matplotlib.pylab as plt

from konlpy.tag import Okt

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from db_connect import DB
from rs_sentiment_analysis.model import LSTM_M

okt = Okt()
db = DB()

# 불용어 리스트
stopwords = ['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']


def save_pickle(data, file_name='test'):
    f = open(file_name + '.pickle', 'wb')
    pickle.dump(data, f)
    f.close()


def load_pickle(file_name='test'):
    f = open(file_name + '.pickle', 'rb')
    data = pickle.load(f)
    f.close()
    return data


# 부정 데이터 로드
sql1 = "select contents, score from restaurant.review where score = 1 or score = 2 and not contents = '' order by rand() limit 5000"
source1 = db.data_load(sql1)

# 긍정 데이터 로드
sql2 = "select contents, score from restaurant.review where score = 4 or score = 5 and not contents = '' order by rand() limit 5000"
source2 = db.data_load(sql2)

source = source1 + source2

# 데이터 정제
data = []
for _source in source:
    temp = []
    if (len(_source[0]) == 0) or (_source[1] == 3):
        continue
    temp.append(_source[0])

    if _source[1] == 1 or _source[1] == 2:
        temp.append(0)
    elif _source[1] == 4 or _source[1] == 5:
        temp.append(1)

    data.append(temp)

# 데이터 셔플
random.shuffle(data)
# 데이터 정리
data = pd.DataFrame(data, columns=['document', 'label'])
# 데이터 분할
train_data, test_data = train_test_split(data, test_size=0.2)

print(train_data)
print(test_data)

# train 데이터 전처리
x_train = []
for sentence in train_data['document']:
    # 토크나이징
    temp_x = okt.morphs(sentence, stem=True)
    # 불용어 제거
    temp_x = [word for word in temp_x if word not in stopwords]
    # 전처리 후 Null 값 제거
    if len(temp_x) != 0:
        x_train.append(temp_x)

# test 데이터 전처리
x_test = []
for sentence in test_data['document']:
    # 토크나이징
    temp_x = okt.morphs(sentence, stem=True)
    # 불용어 제거
    temp_x = [word for word in temp_x if word not in stopwords]
    # 전처리 후 Null 값 제거
    if len(temp_x) != 0:
        x_test.append(temp_x)

# 결과값 label
y_train = train_data['label']
y_test = test_data['label']


# 상위 30,000개의 단어만 보존
max_words = 30000
tokenizer = Tokenizer(num_words=max_words)
tokenizer.fit_on_texts(x_train)

'''
# 리뷰 정보
print('리뷰의 최대 길이 :', max(len(l) for l in x_train))
print('리뷰의 평균 길이 :', sum(map(len, x_train))/len(x_train))
plt.hist([len(s) for s in x_train], bins=50)
plt.xlabel('length of Data')
plt.ylabel('number of Data')
plt.show()
'''

# 토큰 리스트 저장 (idx2token)
idx2token = tokenizer.index_word
save_pickle(idx2token, 'rs_LSTM_model_token')

# 정수 인코딩
x_train = tokenizer.texts_to_sequences(x_train)
x_test = tokenizer.texts_to_sequences(x_test)

# 전체 데이터의 길이 200으로 padding
max_len = 200
x_train = pad_sequences(x_train, maxlen=max_len)
x_test = pad_sequences(x_test, maxlen=max_len)

# 모델 구축
lstm_m = LSTM_M(input_size=max_len, input_dim=max_words, embedding_size=128,
                hidden_size=64, n_classes=2)
model = lstm_m.create_model()

# 모델 훈련
history = model.fit(x_train, y_train, epochs=4, batch_size=64, validation_split=0.2)

# 모델 정확도 평가
print("\n 테스트 정확도: %.3f" % (model.evaluate(x_test, y_test)[1]))

# 모델 저장
save_pickle(model, 'rs_LSTM_model')
