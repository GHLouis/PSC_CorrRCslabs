import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error

class RegressionNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(5, 16), nn.ReLU(), nn.Dropout(0.2),   # input layer
            nn.Linear(16, 16), nn.ReLU(), nn.Dropout(0.2),  # hidden layer
            nn.Linear(16, 1)                                # output layer
        )       
    def forward(self, x):
        return self.network(x)

class NeuralNetworkRegression:
    def __init__(self):
        self.train_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_trainset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.test_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_testset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])

        self.net = None
        self.scaler_X = None
        self.scaler_y = None
        self.feature_num = 0
        self.train_model()

    def train_model(self):
        target_col = "ultimate_strength KN"
        X_train = self.train_df.drop(target_col, axis=1).values
        y_train = self.train_df[target_col].values.reshape(-1, 1)

        X_test = self.test_df.drop(target_col, axis=1).values
        y_test = self.test_df[target_col].values.reshape(-1, 1)

        self.feature_num = X_train.shape[1]

        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        
        X_train_scaled = self.scaler_X.fit_transform(X_train)
        X_test_scaled = self.scaler_X.transform(X_test)
        y_train_scaled = self.scaler_y.fit_transform(y_train)
        y_test_scaled = self.scaler_y.transform(y_test)

        # Change to Tensor
        X_train_tensor = torch.tensor(X_train_scaled, dtype=torch.float32)
        y_train_tensor = torch.tensor(y_train_scaled, dtype=torch.float32)
        X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)

        # DataLoader Packaging 
        train_loader = DataLoader(TensorDataset(X_train_tensor, y_train_tensor), batch_size=16, shuffle=True)

        # Define the model, loss function, and optimizer
        self.net = RegressionNet()
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.net.parameters(), lr=0.001)

        # Train for 500 runs
        self.net.train()
        for epoch in range(800): 
            for features, targets in train_loader:
                outputs = self.net(features)       
                loss = criterion(outputs, targets)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()     

            if (epoch + 1) % 100 == 0:
                print(f'Epoch {epoch+1}, Loss: {loss.item():.4f}')

        # Define the assessment model
        self.net.eval()
        with torch.no_grad():
            train_pred_scaled = self.net(X_train_tensor).numpy()
            test_pred_scaled = self.net(X_test_tensor).numpy()

            # Inverse transform the standardized predicted values
            train_pred = self.scaler_y.inverse_transform(train_pred_scaled)
            test_pred = self.scaler_y.inverse_transform(test_pred_scaled)

            train_r2 = r2_score(y_train, train_pred)
            test_r2 = r2_score(y_test, test_pred)
            train_mse = mean_squared_error(y_train, train_pred)
            test_mse = mean_squared_error(y_test, test_pred)

        print("Finish Neural Network Training!")
        print(f"Feature count detected: {self.feature_num}")
        print(f"Train R² Score: {train_r2:.4f} | Train MSE: {train_mse:.4f}")
        print(f"Test R² Score: {test_r2:.4f} | Test MSE: {test_mse:.4f}")

    def prediction(self):
        if self.net is None:
            return None        
        df = pd.read_csv(r'') # Please input address of files to be predicted
        target_col = "ultimate_strength KN"
        X = df.drop(target_col, axis=1).values if target_col in df.columns else df.values        
        X_scaled = self.scaler_X.transform(X)
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        self.net.eval()
        with torch.no_grad():
            y_pred_scaled = self.net(X_tensor).numpy()
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled)
        
        return float(y_pred[0][0]) if len(y_pred) == 1 else y_pred.flatten().tolist()

if __name__ == "__main__":
    model = NeuralNetworkRegression()