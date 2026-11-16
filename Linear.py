import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge  # 使用带L2正则化的岭回归替代普通线性回归
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error

class LinearRegression:
    def __init__(self):
        self.train_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_trainset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.test_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_testset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.linear = None
        self.X_Scale = None
        self.feature_num = 0
        self.train_model()

    def train_model(self):
        target_col = "ultimate_strength KN"
        self.X_train = self.train_df.drop(target_col, axis=1).values
        self.y_train = self.train_df[target_col].values
        self.X_test = self.test_df.drop(target_col, axis=1).values
        self.y_test = self.test_df[target_col].values
        self.feature_num = self.X_train.shape[1]

        # 正则化
        self.X_Scale = StandardScaler()
        X_train_scaled = self.X_Scale.fit_transform(self.X_train)
        X_test_scaled = self.X_Scale.transform(self.X_test)


        self.linear = Ridge(alpha=0.5)
        self.linear.fit(X_train_scaled, self.y_train)

        # 计算训练集和测试集的 r2
        y_train_pred = self.linear.predict(X_train_scaled)
        train_r2 = r2_score(self.y_train, y_train_pred)
        train_mse = mean_squared_error(self.y_train, y_train_pred)

        y_test_pred = self.linear.predict(X_test_scaled)
        test_r2 = r2_score(self.y_test, y_test_pred)
        test_mse = mean_squared_error(self.y_test, y_test_pred)

        print("Finish Linear Regression (Ridge) Training!")
        print(f"Feature count detected: {self.feature_num}")
        print(f"Train R² Score: {train_r2:.4f} | Train MSE: {train_mse:.4f}")
        print(f"Test R² Score: {test_r2:.4f} | Test MSE: {test_mse:.4f}")

    def prediction(self):
        if self.linear is None:
            return None
        df = pd.read_csv(r'') # 输入需要预测的文件地址
        target_col = "ultimate_strength KN"
        X = df.drop(target_col, axis=1).values if target_col in df.columns else df.values
        input_scale = self.X_Scale.transform(X)
        results = self.linear.predict(input_scale)
        
        return float(results[0]) if len(results) == 1 else results.tolist()

if __name__ == "__main__":
    model = LinearRegression()