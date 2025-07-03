import streamlit as st
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# Import your modules
from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from execution.equities import EquitiesExecutor
from execution.crypto import CryptoExecutor
from execution.options import OptionsExecutor
from simulation.simulator import Simulator
from explainability.shap_explainer import ShapExplainer
from interface.copilot import Copilot

# Configure logger
logger = logging.getLogger("V13Main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s"
)

def main():
    st.set_page_config(
        page_title="V13 Quant App",
        layout="wide"
    )

    # Auto-refresh every 30s
    st_autorefresh = st.experimental_memo(lambda: None, ttl=30)
    st_autorefresh()

    st.title("🚀 V13 Quant System")
    st.write("✅ Alerts, portfolio, and thresholds enabled.")

    # Initialize modules
    ml_ensemble = MLEnsemble()
    rl_agent = RLAgent()
    ensemble_manager = EnsembleManager(weight_rl=0.5)
    equities_exec = EquitiesExecutor()
    crypto_exec = CryptoExecutor()
    options_exec = OptionsExecutor()
    simulator = Simulator()
    explainer = ShapExplainer()
    copilot = Copilot()

    # Session state
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []

    if "positions" not in st.session_state:
        st.session_state.positions = {"AAPL": 0, "BTCUSDT": 0}

    # Load model
    model_loaded = False
    try:
        ml_ensemble.load("models/xgb_model.pkl")
        model_loaded = True
        st.success("✅ ML model loaded.")
    except Exception as e:
        logger.warning(f"Model load failed: {e}")
        st.warning("⚠️ Dummy predictions active.")

    # Layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Market Data")
        try:
            btc_price = float(crypto_exec.client.get_symbol_ticker(symbol="BTCUSDT")["price"])
            st.metric("BTC/USDT", f"${btc_price:,.2f}")
        except:
            btc_price = 0
            st.warning("BTC price unavailable.")

        try:
            aapl_quote = equities_exec.api.get_last_trade("AAPL")
            aapl_price = aapl_quote.price
            st.metric("AAPL", f"${aapl_price:,.2f}")
        except:
            aapl_price = 0
            st.warning("AAPL price unavailable.")

        # Features
        f1 = btc_price
        f2 = aapl_price
        f3 = np.random.uniform(0.01, 0.05)
        f4 = (aapl_price / btc_price) if btc_price > 0 else 0

        ml_input = [[f1, f2, f3, f4]]
        rl_obs = [f3, f4]

        st.write("Features:")
        st.json({"BTC": f1, "AAPL": f2, "Volatility": f3, "Ratio": f4})

        if model_loaded:
            ml_pred = ml_ensemble.model.predict(ml_input)
        else:
            ml_pred = ["0.5"]

        try:
            rl_pred = rl_agent.model.predict(rl_obs)
        except:
            rl_pred = [0.5]

        blended = ensemble_manager.predict(ml_input, rl_obs)
        signal_strength = float(blended[0]) if hasattr(blended, "__getitem__") else blended

        # Thresholds
        st.subheader("Signal Thresholds")
        buy_threshold = st.slider("Buy Threshold", 0.0, 1.0, 0.6, 0.01)
        sell_threshold = st.slider("Sell Threshold", 0.0, 1.0, 0.4, 0.01)

        # Alerts
        st.subheader("Signal")
        if signal_strength > buy_threshold:
            st.success(f"🔵 BUY ALERT! ({signal_strength:.2f})")
        elif signal_strength < sell_threshold:
            st.error(f"🔴 SELL ALERT! ({signal_strength:.2f})")
        else:
            st.warning(f"🟡 Hold/Neutral ({signal_strength:.2f})")

        st.write(f"ML: {ml_pred}, RL: {rl_pred}, Blended: {blended}")

        # SHAP
        st.subheader("SHAP Explanations")
        shap_values = explainer.explain(ml_input)
        df_shap = pd.DataFrame({
            "Feature": [f"F{i+1}" for i in range(len(shap_values))],
            "SHAP": shap_values
        })
        st.bar_chart(df_shap.set_index("Feature"))

    with col2:
        st.subheader("💼 Portfolio Overview")
        btc_pos = st.session_state.positions["BTCUSDT"]
        aapl_pos = st.session_state.positions["AAPL"]
        btc_value = btc_pos * btc_price
        aapl_value = aapl_pos * aapl_price

        st.write(f"BTC Position: {btc_pos} units (${btc_value:.2f})")
        st.write(f"AAPL Position: {aapl_pos} units (${aapl_value:.2f})")

        st.subheader("Trade Controls")
        sim_mode = st.checkbox("Simulation Mode", value=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if st.button("Buy AAPL"):
            if sim_mode:
                st.success("Simulated AAPL buy.")
                st.session_state.trade_log.append({
                    "Time": timestamp,
                    "Asset": "AAPL",
                    "Qty": 10,
                    "Side": "Buy",
                    "Price": aapl_price,
                    "Mode": "Simulated"
                })
                st.session_state.positions["AAPL"] += 10
            else:
                result = equities_exec.submit_order("AAPL", qty=10, side="buy")
                st.success(f"Live order: {result}")
                st.session_state.positions["AAPL"] += 10
                st.session_state.trade_log.append({
                    "Time": timestamp,
                    "Asset": "AAPL",
                    "Qty": 10,
                    "Side": "Buy",
                    "Price": aapl_price,
                    "Mode": "Live"
                })

        if st.button("Buy BTC"):
            if sim_mode:
                st.success("Simulated BTC buy.")
                st.session_state.trade_log.append({
                    "Time": timestamp,
                    "Asset": "BTCUSDT",
                    "Qty": 0.01,
                    "Side": "Buy",
                    "Price": btc_price,
                    "Mode": "Simulated"
                })
                st.session_state.positions["BTCUSDT"] += 0.01
            else:
                result = crypto_exec.submit_order("BTCUSDT", qty=0.01, side="buy")
                st.success(f"Live order: {result}")
                st.session_state.positions["BTCUSDT"] += 0.01
                st.session_state.trade_log.append({
                    "Time": timestamp,
                    "Asset": "BTCUSDT",
                    "Qty": 0.01,
                    "Side": "Buy",
                    "Price": btc_price,
                    "Mode": "Live"
                })

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

if __name__ == "__main__":
    main()
