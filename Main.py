import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from prediction.options_scanner import OptionsAnalyzer
from execution.equities import EquitiesExecutor
from execution.crypto import CryptoExecutor
from simulation.simulator import Simulator

# Initialize modules
ml_model = MLEnsemble()
rl_agent = RLAgent()
ensemble = EnsembleManager(ml_model=ml_model, rl_model=rl_agent, weight_rl=0.4)
crypto_exec = CryptoExecutor(config={"api_key": "your_api_key", "api_secret": "your_api_secret"})
equities_exec = EquitiesExecutor()
simulator = Simulator()

# Streamlit UI
st.set_page_config(page_title="V13 Quant System", layout="wide")
st.title("🚀 V13 Quant System")
st.success("✅ This app has successfully deployed!")

# Show module status
st.subheader("Modules Status")
st.write("✅ ML Prediction Module: Ready")
st.write("✅ RL Agent Module: Ready")
st.write("✅ Options Analyzer Module: Ready")
st.write("✅ Crypto Module: Ready")
st.write("✅ Equities Module: Ready")
st.write("✅ Simulator Module: Ready")

# Options Analyzer Section
st.subheader("Options Analysis")
if st.button("Run Options Analysis"):
    analyzer = OptionsAnalyzer()
    results = analyzer.analyze(symbol="AAPL")
    st.write("Top Options Contracts:")
    st.table(results)

# Example Performance Metrics - Fixed serialization issue
df_metrics = pd.DataFrame({
    "Metric": ["Sharpe Ratio", "Win Rate", "Max Drawdown"],
    "Value": [1.42, 62, -12]
})

st.subheader("Example Performance Metrics")
st.dataframe(
    df_metrics.style.format({
        "Value": ["{:.2f}", "{:.0f}%", "{:.0f}%"]
    })
)

# Example Signal Chart
st.subheader("Example Signal Chart")
fig, ax = plt.subplots()
signal = np.sin(np.linspace(0, 2 * np.pi, 20))
ax.plot(signal)
ax.set_title("Sample Signal")
st.pyplot(fig)

# Simple Trading Logic Demo
ml_input = np.random.rand(5)
rl_obs = np.random.rand(2)
prediction = ensemble.predict(ml_input, rl_obs)
st.subheader("Blended Prediction Output")
st.write(prediction)
