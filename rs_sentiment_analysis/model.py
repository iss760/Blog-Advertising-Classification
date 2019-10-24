import keras
from keras.layers import Input, Embedding, LSTM, Dense
from keras.models import Model


class LSTM_M:
    def __init__(self, input_size, input_dim, embedding_size, hidden_size, n_classes, drop_out=0.5,
                 optimizer='rmsprop', loss_function='binary_crossentropy'):
        self.input_size = input_size
        self.input_dim = input_dim
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.n_classes = n_classes
        self.drop_out = drop_out
        self.optimizer = optimizer
        self.loss_function = loss_function

    def create_model(self):
        # 입력 값
        main_input = Input(shape=(self.input_size,), dtype='int32', name='main_input')

        # 임베딩 층
        x = Embedding(output_dim=self.embedding_size, input_dim=self.input_dim, input_length=self.input_size)(main_input)

        # LSTM 층
        lstm_out = LSTM(self.hidden_size, dropout=self.drop_out)(x)

        # 출력 층
        main_output = Dense(1, activation='sigmoid', name='main_output')(lstm_out)

        # 모델
        model = Model(inputs=main_input, outputs=main_output)

        # 모델 컴파일
        model.compile(optimizer=self.optimizer, loss=self.loss_function, metrics=['acc'])

        return model
