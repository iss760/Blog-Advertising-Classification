import torch.nn as nn
import torch
from torch.autograd import Variable


class Sentiment_Analysis_LSTM(nn.Module):
    def __init__(self, token2idx, max_sequence, vocab_size, embed_size, hid_size,
                 n_layers, dropout, bidirectional, n_category):
        """
        :param token2idx: (list) 고유한 단어의 리스트
        :param max_sequence: (int) 한 문장의 최대 길이
        :param vocab_size: (int) 고유한 단어의 수
        :param embed_size: (int) 임베딩 차원의 크기
        :param hid_size: (int) LSTM 뉴런의 개수
        :param n_layers: (int) LSTM layer 수
        :param dropout: (float) 드롭아웃
        :param bidirectional: (bool) bidirectional 유무
        :param n_category: (int) 분류 카테고리 개수
        """
        super(Sentiment_Analysis_LSTM, self).__init__()

        self.max_sequence = max_sequence
        self.vocab_size = vocab_size
        self.embed_size = embed_size
        self.hid_size = hid_size
        self.n_layers = n_layers
        self.drouput = dropout
        self.bidirectional = bidirectional
        self.n_category = n_category

        self.padding_index = token2idx['<PAD>']

        self.embed = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embed_size,
            padding_idx=self.padding_index
        )

        self.lstm = nn.LSTM(embed_size, hid_size, n_layers, batch_first=True, bidirectional=True)

        if bidirectional:
            input_dim = 2 * hid_size * max_sequence
        else:
            input_dim = hid_size * max_sequence

        self.lin = nn.Linear(input_dim, n_category)
        self.outputs = []

    def init_hidden(self, batch_size):
        # 최초에 h_0와 c_0의 초기값 부여 (n_layers, batch_size, hid_size(n_neuron))
        # bidirectional True 일 경우, (2*n_layers, batch_size, hid_size)
        if self.bidirectional:
            h_0 = Variable(torch.randn(2 * self.n_layers, batch_size, self.hid_size)) * 0.1
            c_0 = Variable(torch.randn(2 * self.n_layers, batch_size, self.hid_size)) * 0.1
        else:
            h_0 = Variable(torch.randn(self.n_layers, batch_size, self.hid_size)) * 0.1
            c_0 = Variable(torch.randn(self.n_layers, batch_size, self.hid_size)) * 0.1

        return h_0, c_0

    def forward(self, x, x_sequence_length):
        # init h randomly
        batch_size = x.size(0)
        self.h_c = self.init_hidden(batch_size)

        # embedding
        x = self.embed(x)  # sequence_length(max_len), batch_size, embed_size

        # packing for LSTM
        x = torch.nn.utils.rnn.pack_padded_sequence(x, x_sequence_length, batch_first=True)

        # LSTM
        output, self.h_c = self.lstm(x, self.h_c)

        # unpack
        # unpacking 과정에서, size(1) S가 가장 긴 sequence 길이를 갖는 data 에 맞춰진다.
        # S가 max_sequence_length 로 고정되는 것이 아님을 주의
        x, _ = torch.nn.utils.rnn.pad_packed_sequence(output, batch_first=True)
        # print(x.shape)

        # flatten
        x = x.contiguous()
        x = x.view(batch_size, -1)

        # fully-connect
        logit = self.lin(x)

        return logit



