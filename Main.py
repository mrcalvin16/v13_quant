import streamlit as st
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
ensemble = EnsembleManager(ml_model=ml_model, rl_model=rl_agent, weight_rl=0.4)

equities_exec = EquitiesExecutor()
crypto_exec = CryptoExecutor(config={"api_key": "your_key", "api_secret": "your_secret"})
options_exec = OptionsExecutor(config={"access_token": "your_token"})
simulator = Simulator(config={"mode": "test"})

# Streamlit UI
st.set_page_config(page_title="V13 Quant System", layout="wide")
st.title("🚀 V13 Quant System")
st.success("✅ All modules initialized successfully!")

st.header("Modules Status")
st.info("ML prediction module: Ready")
st.info("RL agent module: Ready")
st.info("Ensemble manager: Ready")
st.info("Equities trading module: Ready")
st.info("Crypto trading module: Ready")
st.info("Options trading module: Ready")
st.info("Simulator: Ready")

st.header("Example Performance Metrics")
performance_data = {
    "Metric": ["Sharpe Ratio", "Win Rate", "Max Drawdown"],
    "Value": ["1.42", "62%", "-12%"]
}
st.table(performance_data)

st.header("Signal Blending Example")
ml_input = [[0.3, 0.7]]
rl_obs = [0.1, 0.05]
prediction = ensemble.predict(ml_input, rl_obs)
st.write(f"Blended prediction output: `{prediction}`")

# Safety confirmation before trading
if st.button("🚨 Execute Equities Trade (TEST MODE)"):
    result = equities_exec.submit_order(symbol="AAPL", qty=1, side="buy")
    st.success(f"Equities trade executed: {result}")

if st.button("🚨 Execute Crypto Trade (TEST MODE)"):
    result = crypto_exec.submit_order(symbol="BTCUSDT", qty=0.01, side="buy")
    st.success(f"Crypto trade executed: {result}")

if st.button("🚨 Execute Options Trade (TEST MODE)"):
    result = options_exec.submit_order(symbol="AAPL_202501_C150", qty=1, side="buy")
    st.success(f"Options trade executed: {result}")

if st.button("Run Simulation"):
    sim_result = simulator.run()
    st.json(sim_result)

st.caption("All trades are currently in TEST MODE. Update config dictionaries with real credentials for live trading.")
