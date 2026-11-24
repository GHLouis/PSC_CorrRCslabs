import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error

class KNNRegression:
    def __init__(self):
        self.train_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_trainset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.test_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_testset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.knn = None
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

        # Regularization
        self.X_Scale = StandardScaler()
        X_train_scaled = self.X_Scale.fit_transform(self.X_train)
        X_test_scaled = self.X_Scale.transform(self.X_test)

        # KNN grid search
        param_grid = {
            'n_neighbors': [3, 5, 7, 9, 11, 13],   # The number of neighbors
            'weights': ['uniform', 'distance']   # The weighting strategy
        }

        # LOOCV based assessment
        loocv = LeaveOneOut()
        knn = KNeighborsRegressor()

        self.knn = KNeighborsRegressor(n_neighbors=3, metric='manhattan', weights='uniform')
        self.knn.fit(X_train_scaled, self.y_train)

        # Calculate r2 for training and testing sets
        y_train_pred = self.knn.predict(X_train_scaled)
        train_r2 = r2_score(self.y_train, y_train_pred)
        train_mse = mean_squared_error(self.y_train, y_train_pred)

        y_test_pred = self.knn.predict(X_test_scaled)
        test_r2 = r2_score(self.y_test, y_test_pred)
        test_mse = mean_squared_error(self.y_test, y_test_pred)

        print("Finish KNN Regression Training!")
        print(f"Feature count detected: {self.feature_num}")
        print(f"Train R² Score: {train_r2:.4f} | Train MSE: {train_mse:.4f}")
        print(f"Test R² Score: {test_r2:.4f} | Test MSE: {test_mse:.4f}")

    def prediction(self):
        if self.knn is None:
            return None
        df = pd.read_csv(r'') # Please input address of files to be predicted
        target_col = "ultimate_strength KN"
        X = df.drop(target_col, axis=1).values if target_col in df.columns else df.values
        
        input_scale = self.X_Scale.transform(X)
        results = self.knn.predict(input_scale)
        
        return float(results[0]) if len(results) == 1 else results.tolist()

if __name__ == "__main__":
    model = KNNRegression()