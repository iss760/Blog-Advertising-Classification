import torch
import torch.nn as nn
from torch.autograd import Variable

import pickle
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score

from posting_feture_classification.model import Net
from db_connect import DB


def save_pickle(data, file_name='test'):
    f = open(file_name + '.pickle', 'wb')
    pickle.dump(data, f)
    f.close()

net = Net()
db = DB()

sql = "SELECT posting_length, posting_picture, posting_video, posting_map, advertisement " \
      "FROM blog.blog_restaurant2 as br left join blog.blogger_list2 as bl on br.blogger = bl.blogger " \
      "where bl.advertisement is not NULL " \
      "order by rand();"
source = db.data_load(sql)
data = []
for _source in source:
    temp = [_source[0], _source[1], _source[2], _source[3], _source[4]]
    data.append(temp)

data = pd.DataFrame(data, columns=['length', 'pictures', 'videos', 'maps', 'advertisement'])

data.loc[data.advertisement == 'Y', 'advertisement'] = 0
data.loc[data.advertisement == 'N', 'advertisement'] = 1

train_x, test_x, train_y, test_y = train_test_split(data[data.columns[:4]].values,
                                                    data.advertisement.values, test_size=0.01)

train_x = Variable(torch.Tensor(train_x).float())
test_x = Variable(torch.Tensor(test_x).float())
train_y = Variable(torch.Tensor(train_y).long())
test_y = Variable(torch.Tensor(test_y).long())

print(train_x.shape, train_y.shape)

model = Net()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

for epoch in range(2000):
    optimizer.zero_grad()
    out = model(train_x)
    loss = criterion(out, train_y)
    loss.backward()
    optimizer.step()

    if epoch % 200 == 0:
        print('number of epoch', epoch, 'loss', loss.data)

predict_out = model(test_x)
_, predict_y = torch.max(predict_out, 1)
print('prediction accuracy', accuracy_score(test_y.data, predict_y.data))

save_pickle(model, 'ad_nn_model')
