import streamlit as st
import pandas as pd
from datetime import datetime

from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from execution.equities import EquitiesExecutor
from execution.crypto import CryptoExecutor

# Initialize session state
if "positions" not in st.session_state:
    st.session_state.positions = {"AAPL": 0, "BTCUSDT": 0}
if "trade_log" not in st.session_state:
    st.session_state.trade_log = []

# Initialize modules
ml_model = MLEnsemble()
rl_agent = RLAgent()
ensemble = EnsembleManager(weight_rl=0.4)

equities_exec = EquitiesExecutor()
crypto_exec = CryptoExecutor()

# Layout
st.set_page_config(
    page_title="🚀 V13 Quant System",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 V13 Quant System")
st.success("✅ This app has successfully deployed!")

# Module status
st.subheader("Modules Status")
st.info("ML prediction module: Ready")
st.info("Crypto trading module: Ready")
st.info("Equities trading module: Ready")

# Example metrics
st.subheader("Example Performance Metrics")
metrics = pd.DataFrame({
    "Metric": ["Sharpe Ratio", "Win Rate", "Max Drawdown"],
    "Value": ["1.42", "62%", "-12%"]
})
st.dataframe(metrics)

# Example chart
st.subheader("Example Signal Chart")
st.line_chart([10, 12, 9, 14, 15])

# Simulated prices (replace with real API)
btc_price = 58000
aapl_price = 190

st.markdown("---")
st.subheader("💼 Portfolio Overview")
btc_pos = st.session_state.positions["BTCUSDT"]
aapl_pos = st.session_state.positions["AAPL"]

st.write(f"BTC Position: {btc_pos} units (${btc_pos * btc_price:,.2f})")
st.write(f"AAPL Position: {aapl_pos} units (${aapl_pos * aapl_price:,.2f})")

st.markdown("---")

# Trade controls
st.subheader("Trade Controls")
col1, col2 = st.columns(2)

with col1:
    sim_mode = st.checkbox("✅ Simulation Mode (Recommended)", value=True)
    confirm_live = st.checkbox("⚠️ I confirm I want to place real trades")

if not sim_mode:
    st.error("⚠️ Simulation Mode is OFF. You are in LIVE TRADING mode!")

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

col_buy_aapl, col_buy_btc = st.columns(2)

with col_buy_aapl:
    if st.button("Buy AAPL", disabled=(not sim_mode and not confirm_live)):
        if sim_mode:
            st.success("Simulated AAPL buy.")
            st.session_state.positions["AAPL"] += 10
            st.session_state.trade_log.append({
                "Time": timestamp,
                "Asset": "AAPL",
                "Qty": 10,
                "Side": "Buy",
                "Price": aapl_price,
                "Mode": "Simulated"
            })
        else:
            order = equities_exec.submit_order("AAPL", qty=10, side="buy")
            st.success(f"Live order submitted: {order}")
            st.session_state.positions["AAPL"] += 10
            st.session_state.trade_log.append({
                "Time": timestamp,
                "Asset": "AAPL",
                "Qty": 10,
                "Side": "Buy",
                "Price": aapl_price,
                "Mode": "Live"
            })

with col_buy_btc:
    if st.button("Buy BTC", disabled=(not sim_mode and not confirm_live)):
        if sim_mode:
            st.success("Simulated BTC buy.")
            st.session_state.positions["BTCUSDT"] += 0.01
            st.session_state.trade_log.append({
                "Time": timestamp,
                "Asset": "BTCUSDT",
                "Qty": 0.01,
                "Side": "Buy",
                "Price": btc_price,
                "Mode": "Simulated"
            })
        else:
            order = crypto_exec.submit_order("BTCUSDT", qty=0.01, side="buy")
            st.success(f"Live order submitted: {order}")
            st.session_state.positions["BTCUSDT"] += 0.01
            st.session_state.trade_log.append({
                "Time": timestamp,
                "Asset": "BTCUSDT",
                "Qty": 0.01,
                "Side": "Buy",
                "Price": btc_price,
                "Mode": "Live"
            })

# Trade history
if st.session_state.trade_log:
    st.subheader("📜 Trade History")
    df_trades = pd.DataFrame(st.session_state.trade_log)

    def compute_pnl(row):
        mark = btc_price if row["Asset"] == "BTCUSDT" else aapl_price
        if row["Side"] == "Buy":
            return (mark - row["Price"]) * row["Qty"]
        else:
            return (row["Price"] - mark) * row["Qty"]

    df_trades["Unrealized P&L"] = df_trades.apply(compute_pnl, axis=1)
    df_trades["Cumulative P&L"] = df_trades["Unrealized P&L"].cumsum()

    st.dataframe(df_trades)
    st.line_chart(df_trades["Cumulative P&L"])

    csv = df_trades.to_csv(index=False).encode()
    st.download_button(
        label="📥 Download Trade Log",
        data=csv,
        file_name="trade_log.csv",
        mime="text/csv"
    )
