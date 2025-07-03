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
ensemble = EnsembleManager(ml_model=ml_model, rl_model=rl_agent, weight_rl=0.4)

# Initialize executors with safe credentials
equities_exec = EquitiesExecutor()

crypto_exec = CryptoExecutor(config={
    "api_key": st.secrets["pCXCN5WRUYVZC9pnSZ7pWbhusJTNkOhsYDQxZly3EpWIuqmZQlQmbe3JMJywVl7r"],
    "api_secret": st.secrets["CxQQvsgG72yoPHc2cd4WGHJ44KeyIBdbc7xQHtMbDa4UICk6VSrfHS79MTTvZzE2"]
})

options_exec = OptionsExecutor(config={
    "access_token": st.secrets.get("TRADIER_ACCESS_TOKEN", "dummy_token")
})

# Initialize simulator
simulator = Simulator()

# Streamlit UI
st.set_page_config(page_title="V13 Quant System", layout="wide")

st.title("🚀 V13 Quant System")
st.success("✅ All modules initialized successfully!")

# Module status
st.subheader("Modules Status")
cols = st.columns(3)
cols[0].info("ML Model: Ready")
cols[1].info("RL Agent: Ready")
cols[2].info("Ensemble Manager: Ready")
st.info("Equities Trading Module: Ready")
st.info("Crypto Trading Module: Ready")
st.info("Options Trading Module: Ready")
st.info("Simulator Module: Ready")

# Example metrics
st.subheader("Example Performance Metrics")
metrics_df = pd.DataFrame({
    "Metric": ["Sharpe Ratio", "Win Rate", "Max Drawdown"],
    "Value": [1.42, "62%", "-12%"]
})
st.table(metrics_df)

# Example blended prediction
st.subheader("Signal Blending Example")
ml_input = [[0.3, 0.7]]
rl_obs = [0.1, 0.05]
prediction = ensemble.predict(ml_input, rl_obs)
st.write(f"Blended prediction: `{prediction}`")

# Safety confirmation
st.subheader("Trading Controls")
sim_mode = st.checkbox("✅ Simulation Mode (Recommended)", value=True)
confirm_live = st.checkbox("⚠️ I confirm I want to place live trades")

if not sim_mode:
    st.error("⚠️ Simulation Mode is OFF! You must confirm above to place real trades.")

# Trading action buttons
col1, col2, col3 = st.columns(3)

if col1.button("Run Simulation"):
    result = simulator.run()
    st.write(result)

if col2.button("Submit Crypto Test Order", disabled=(not sim_mode and not confirm_live)):
    if sim_mode:
        st.success("Simulated Crypto order.")
    else:
        order = crypto_exec.submit_order(symbol="BTCUSDT", qty=0.01, side="buy")
        st.success(f"Live Crypto order placed: {order}")

if col3.button("Submit Equities Test Order", disabled=(not sim_mode and not confirm_live)):
    if sim_mode:
        st.success("Simulated Equities order.")
    else:
        order = equities_exec.submit_order(symbol="AAPL", qty=1, side="buy")
        st.success(f"Live Equities order placed: {order}")

if st.button("Submit Options Test Order", disabled=(not sim_mode and not confirm_live)):
    if sim_mode:
        st.success("Simulated Options order.")
    else:
        order = options_exec.submit_order(symbol="AAPL_20240719_150_C", qty=1, side="buy")
        st.success(f"Live Options order placed: {order}")

st.caption("✅ All trades default to simulation mode unless explicitly confirmed.")
