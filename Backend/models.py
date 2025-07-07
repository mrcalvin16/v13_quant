import joblib
import numpy as np

model = joblib.load("xgboost_model.pkl")

def get_prediction_score(ticker):
    features = np.array([0.5, 0.3, 0.2]).reshape(1, -1)
    prob = model.predict_proba(features)[0][1]
    return float(prob)

def get_predicted_price(ticker):
    return 500.0
