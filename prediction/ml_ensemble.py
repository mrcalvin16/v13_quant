import joblib
import xgboost as xgb

class MLEnsemble:
    def __init__(self):
        self.model = None

    def train(self, X_train, y_train):
        self.model = xgb.XGBRegressor(n_estimators=100)
        self.model.fit(X_train, y_train)

    def predict(self, X):
        return self.model.predict(X)

    def save(self, path):
        joblib.dump(self.model, path)

    def load(self, path):
        self.model = joblib.load(path)
