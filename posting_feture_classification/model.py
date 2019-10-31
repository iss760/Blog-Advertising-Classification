import torch.nn as nn
import torch.nn.functional as F

class Net(nn.Module):
    # define nn model
    def __init__(self):
        super(Net, self).__init__()

        self.fc1 = nn.Linear(4, 4)
        self.fc2 = nn.Linear(4, 4)
        self.fc3 = nn.Linear(4, 2)
        self.sigmoid = nn.Sigmoid()

    def forward(self, X):
        X = F.relu(self.fc1(X))
        X = self.fc2(X)
        X = self.fc3(X)
        X = self.sigmoid(X)

        return X
