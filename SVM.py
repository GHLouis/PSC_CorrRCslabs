import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error

class SVMRegression:
    def __init__(self):
        self.train_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_trainset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.test_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_testset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.svm = None
        self.X_Scale = None
        self.y_Scale = None
        self.feature_num = 0
        self.train_model()

    def train_model(self):
        target_col = "ultimate_strength KN"
        self.X_train = self.train_df.drop(target_col, axis=1).values
        self.y_train = self.train_df[target_col].values
        self.X_test = self.test_df.drop(target_col, axis=1).values
        self.y_test = self.test_df[target_col].values
        self.feature_num = self.X_train.shape[1]

        # Regularization
        self.X_Scale = StandardScaler()
        self.y_Scale = StandardScaler()

        X_train_scaled = self.X_Scale.fit_transform(self.X_train)
        X_test_scaled = self.X_Scale.transform(self.X_test)

        y_train_scaled = self.y_Scale.fit_transform(self.y_train.reshape(-1, 1)).ravel()

        # Support Vector Machine grid search
        self.svm = SVR(
            kernel='rbf',
            C=27,
            gamma=0.080,
            epsilon=0.086
        )

        self.svm.fit(X_train_scaled, y_train_scaled)

        # Calculate r2 for training and testing sets
        y_train_pred_scaled = self.svm.predict(X_train_scaled)
        y_train_pred = self.y_Scale.inverse_transform(y_train_pred_scaled.reshape(-1, 1)).ravel()
        train_r2 = r2_score(self.y_train, y_train_pred)
        train_mse = mean_squared_error(self.y_train, y_train_pred)

        # Evaluate test set performance
        y_test_pred_scaled = self.svm.predict(X_test_scaled)
        y_test_pred = self.y_Scale.inverse_transform(y_test_pred_scaled.reshape(-1, 1)).ravel()
        test_r2 = r2_score(self.y_test, y_test_pred)
        test_mse = mean_squared_error(self.y_test, y_test_pred)

        print("Finish SVM Training!")
        print(f"Feature count detected: {self.feature_num}")
        print(f"Train R² Score: {train_r2:.4f} | Train MSE: {train_mse:.4f}")
        print(f"Test R² Score: {test_r2:.4f} | Test MSE: {test_mse:.4f}")

    def prediction(self):
        if self.svm is None:
            return None
        df = pd.read_csv(r"") # Please input address of files to be predicted
        target_col = "ultimate_strength KN"
        X = df.drop(target_col, axis=1).values if target_col in df.columns else df.values
        input_scale = self.X_Scale.transform(X)
        results_scaled = self.svm.predict(input_scale)
        results = self.y_Scale.inverse_transform(results_scaled.reshape(-1, 1)).ravel()
        
        return float(results[0]) if len(results) == 1 else results.tolist()

if __name__ == "__main__":
    model = SVMRegression()