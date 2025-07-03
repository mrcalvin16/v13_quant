import streamlit as st
import pandas as pd
from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from execution.equities import EquitiesExecutor
from execution.crypto import CryptoExecutor
from execution.options import OptionsExecutor
from simulation.simulator import Simulator

# Initialize models
ml_model = MLEnsemble()
rl_agent = RLAgent()

ensemble = EnsembleManager(
    ml_model=ml_model,
    rl_model=rl_agent,
    weight_rl=0.4
)

# Initialize executors using Streamlit secrets
crypto_exec = CryptoExecutor(config={
    "api_key": st.secrets["BINANCE_API_KEY"],
    "api_secret": st.secrets["BINANCE_SECRET_KEY"]
})

options_exec = OptionsExecutor(config={
    "access_token": st.secrets["TRADIER_ACCESS_TOKEN"]
})

equities_exec = EquitiesExecutor()
simulator = Simulator()

# Streamlit UI
st.set_page_config(page_title="V13 Quant System", layout="wide")

st.title("🚀 V13 Quant System")
st.success("✅ App loaded successfully.")

st.subheader("Modules Status")
st.info("ML Prediction Module: Ready")
st.info("RL Agent Module: Ready")
st.info("Crypto Trading Module: Ready")
st.info("Options Trading Module: Ready")
st.info("Equities Trading Module: Ready")

# Example Metrics
st.subheader("Example Performance Metrics")
metrics_data = {
    "Metric": ["Sharpe Ratio", "Win Rate", "Max Drawdown"],
    "Value": [1.42, "62%", "-12%"]
}
df_metrics = pd.DataFrame(metrics_data)
st.table(df_metrics)

# Example blended signal chart
st.subheader("Example Signal Chart")
example_signal = pd.Series([10, 12, 9, 14, 15, 13])
st.line_chart(example_signal)

# Trade Execution Buttons with safety confirmation
st.subheader("Trade Execution")
if st.button("Submit Test Order (Simulation Only)"):
    with st.spinner("Submitting test order..."):
        result = simulator.run()
    st.success(f"Simulation Result: {result}")

if st.button("Submit Real Crypto Order (Binance)"):
    confirm = st.radio("Are you sure you want to submit a live Binance order?", ["No", "Yes"])
    if confirm == "Yes":
        with st.spinner("Submitting live Binance order..."):
            response = crypto_exec.submit_order(symbol="BTCUSDT", qty=0.001, side="buy")
        st.success(f"Binance Order Response: {response}")

if st.button("Submit Real Equities Order"):
    confirm = st.radio("Are you sure you want to submit a live Equities order?", ["No", "Yes"])
    if confirm == "Yes":
        with st.spinner("Submitting live Equities order..."):
            response = equities_exec.submit_order(symbol="AAPL", qty=1, side="buy")
        st.success(f"Equities Order Response: {response}")

if st.button("Submit Real Options Order"):
    confirm = st.radio("Are you sure you want to submit a live Options order?", ["No", "Yes"])
    if confirm == "Yes":
        with st.spinner("Submitting live Options order..."):
            response = options_exec.submit_order(symbol="AAPL_20240119C150", qty=1, side="buy")
        st.success(f"Options Order Response: {response}")

st.caption("Use at your own risk. This is a prototype.")
