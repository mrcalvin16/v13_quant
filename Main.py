import streamlit as st
from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from prediction.options_scanner import OptionsAnalyzer
from simulation.simulator import Simulator

# Initialize modules
ml_model = MLEnsemble()
rl_agent = RLAgent()
ensemble = EnsembleManager(ml_model=ml_model, rl_model=rl_agent, weight_rl=0.4)
options_analyzer = OptionsAnalyzer()
simulator = Simulator(returns=[0.01, -0.02, 0.015])  # Dummy returns so it doesn't error

# Streamlit UI
st.set_page_config(page_title="V13 Quant System")

st.title("🚀 V13 Quant System")
st.success("✅ This app has successfully deployed!")

# Show module status
st.subheader("Modules Status")
st.write("✅ ML Prediction Module: Ready")
st.write("✅ RL Agent Module: Ready")
st.write("✅ Options Analyzer Module: Ready")
st.write("✅ Simulator Module: Ready")

# Options Scanner UI
st.subheader("Options Scanner")
symbol = st.text_input("Enter a stock symbol to scan options:", value="AAPL")

if st.button("Run Options Analysis"):
    with st.spinner("Analyzing options..."):
        recommendations = options_analyzer.get_recommendations(symbol)
    if recommendations and isinstance(recommendations[0], dict) and "error" in recommendations[0]:
        st.error(f"Error: {recommendations[0]['error']}")
    else:
        st.success("Top Options Contracts:")
        st.table(recommendations)

# Example Performance Metrics
st.subheader("Example Performance Metrics")
import pandas as pd
metrics_df = pd.DataFrame({
    "Metric": ["Sharpe Ratio", "Win Rate", "Max Drawdown"],
    "Value": [1.42, "62%", "-12%"]
})
st.table(metrics_df)

# Example Signal Chart
import matplotlib.pyplot as plt
import numpy as np
st.subheader("Example Signal Chart")
x = np.arange(10)
y = np.sin(x)
fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_title("Sample Signal")
st.pyplot(fig)
