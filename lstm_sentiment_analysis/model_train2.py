import pickle
import pandas as pd

from konlpy.tag import Okt

from keras.preprocessing.text import Tokenizer
from keras.layers import Embedding, Dense, LSTM
from keras.models import Sequential
from keras.preprocessing.sequence import pad_sequences

from data_setup.tokenizer import KrTokenizer

okt = Okt()
krt = KrTokenizer()

# 불용어 리스트
stopwords = ['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']

# 데이터 로드
train_data = pd.read_table('./ratings_train.txt')
test_data = pd.read_table('./ratings_test.txt')

# 초기 Null 값 제거
train_data = train_data.dropna(how='any')
test_data = test_data.dropna(how='any')

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

# 상위 35,000개의 단어만 보존
max_words = 35000
tokenizer = Tokenizer(num_words=max_words)
tokenizer.fit_on_texts(x_train)

# 토큰 리스트 저장 (idx2token)
f = open('LSTM_model2_token.pickle', 'wb')
idx2token = tokenizer.index_word
pickle.dump(idx2token, f)
f.close()

# 정수 인코딩
x_train = tokenizer.texts_to_sequences(x_train)
x_test = tokenizer.texts_to_sequences(x_test)

# 결과값 label
y_train = train_data['label']
y_test = test_data['label']

# 전체 데이터의 길이 30으로 padding
max_len = 30
x_train = pad_sequences(x_train, maxlen=max_len)
x_test = pad_sequences(x_test, maxlen=max_len)

# 모델 구축
model = Sequential()
model.add(Embedding(max_words, 100))
model.add(LSTM(128))
model.add(Dense(1, activation='sigmoid'))

# 모델 훈련
model.compile(optimizer='rmsprop', loss='binary_crossentropy', metrics=['acc'])
history = model.fit(x_train, y_train, epochs=4, batch_size=60, validation_split=0.2)

# 모델 정확도 평가
print("\n 테스트 정확도: %.3f" % (model.evaluate(x_test, y_test)[1]))

# 모델 저장
f = open('LSTM_model2.pickle', 'wb')
pickle.dump(model, f)
f.close()
