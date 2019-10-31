import pickle

import torch
from torch.autograd import Variable

class Posting_Classification:
    def __init__(self):
        self.model_path = './ad_nn_model'

    def load_pickle(self, file_name='test'):
        f = open(file_name + '.pickle', 'rb')
        data = pickle.load(f)
        f.close()
        return data

    def classification(self, length, pictures, videos, maps):
        model = self.load_pickle(self.model_path)
        data = [[length, pictures, videos, maps]]
        print(data)

        pred_x = Variable(torch.Tensor(data).float())

        predict_out = model(pred_x)
        _, predict_y = torch.max(predict_out, 1)

        print(int(predict_y))
