import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error

class ForestRegression:
    def __init__(self):
        self.train_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_trainset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.test_df = pd.read_csv(r'C:\Users\DIY\Desktop\machine learning\fem_testset.csv', usecols=['x1', 'x2', 'x3', 'x4', 'x5', 'ultimate_strength KN'])
        self.forest = None
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

        # Random Forest grid search (by limiting tree depth and leaf nodes to prevent overfitting)
        self.forest = RandomForestRegressor(n_estimators=120,max_depth=12,min_samples_leaf=1,min_samples_split=2,random_state=42)
        self.forest.fit(X_train_scaled, self.y_train)

        # Calculate r2 for training and testing sets
        y_train_pred = self.forest.predict(X_train_scaled)
        train_r2 = r2_score(self.y_train, y_train_pred)
        train_mse = mean_squared_error(self.y_train, y_train_pred)

        y_test_pred = self.forest.predict(X_test_scaled)
        test_r2 = r2_score(self.y_test, y_test_pred)
        test_mse = mean_squared_error(self.y_test, y_test_pred)

        print("Finish Random Forest Training!")
        print(f"Feature count detected: {self.feature_num}")
        print(f"Train R² Score: {train_r2:.4f} | Train MSE: {train_mse:.4f}")
        print(f"Test R² Score: {test_r2:.4f} | Test MSE: {test_mse:.4f}")

    def prediction(self):
        if self.forest is None:
            return None
        df = pd.read_csv(r'') # Please input address of files to be predicted
        target_col = "ultimate_strength KN"
        X = df.drop(target_col, axis=1).values if target_col in df.columns else df.values
        input_scale = self.X_Scale.transform(X)
        results = self.forest.predict(input_scale)
        
        return float(results[0]) if len(results) == 1 else results.tolist()

if __name__ == "__main__":
    model = ForestRegression()