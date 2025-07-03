import streamlit as st
import pandas as pd
from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from execution.equities import EquitiesExecutor
from execution.crypto import CryptoExecutor
from execution.options import OptionsExecutor
from simulation.simulator import Simulator

# Initialize modules
ml_model = MLEnsemble()
rl_agent = RLAgent()
ensemble = EnsembleManager(
    ml_model=ml_model,
    rl_model=rl_agent,
    weight_rl=0.4
)
equities_exec = EquitiesExecutor()
crypto_exec = CryptoExecutor(config={})
options_exec = OptionsExecutor()
simulator = Simulator()

# Streamlit UI
st.set_page_config(page_title="🚀 V13 Quant System", layout="wide")
st.title("🚀 V13 Quant System")
st.success("✅ App initialized successfully!")

# Module status
st.subheader("Module Status")
cols = st.columns(3)
cols[0].info("ML Model: Ready")
cols[1].info("RL Agent: Ready")
cols[2].info("Ensemble Manager: Ready")

# Safety confirmation
st.warning("⚠️ **Important:** This platform can execute real trades. Confirm below before enabling execution.")
confirm = st.checkbox("I understand the risks and want to enable live trading.")
if confirm:
    st.success("✅ Live trading is ENABLED.")
else:
    st.error("🚫 Live trading is DISABLED. Simulation mode only.")

# Example prediction
st.subheader("Example Prediction")
ml_input = [[0.2, 0.4, 0.6]]
rl_obs = [0.1, 0.05]
prediction = ensemble.predict(ml_input, rl_obs)
st.write(f"Blended prediction: **{prediction:.4f}**")

# Simple threshold logic
if prediction > 0.5 and confirm:
    st.success("📈 Signal: BUY")
    equities_exec.submit_order(symbol="AAPL", quantity=1, side="buy")
else:
    st.info("No trade action triggered.")

# Example performance metrics
st.subheader("Example Performance Metrics")
metrics_df = pd.DataFrame({
    "Metric": ["Sharpe Ratio", "Win Rate", "Max Drawdown"],
    "Value": [1.42, 62, -12]
})
st.table(metrics_df)

# Example signal chart
st.subheader("Example Signal Chart")
chart_data = pd.DataFrame({
    "Signal": [10, 12, 9, 15, 14]
})
st.line_chart(chart_data)

st.caption("© V13 Quant System — for research and educational purposes only.")
