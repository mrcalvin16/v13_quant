import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objs as go
import yfinance as yf

API_URL = "https://v13-quant.onrender.com"

st.title("🚀 Quant Trading Dashboard (No Login)")

# Load tickers
r = httpx.get(f"{API_URL}/tickers")
tickers_list = r.json()

ticker = st.selectbox("Select Ticker:", tickers_list)

if st.button("Get Recommendation"):
    with st.spinner("Fetching data..."):
        r = httpx.get(f"{API_URL}/recommendation/{ticker}")
        rec = r.json()
        st.subheader("📈 Recommendation Details")
        st.json(rec)

        # Chart
        st.subheader("📊 Historical Prices & Prediction")
        data = yf.Ticker(ticker).history(period="6mo")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name="Historical Close"
        ))

        if "pred_price" in rec:
            fig.add_trace(go.Scatter(
                x=[data.index[-1], data.index[-1]],
                y=[data["Close"].iloc[-1], rec["pred_price"]],
                mode="lines+markers",
                name="Predicted Target",
                line=dict(dash="dot")
            ))

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_dark"
        )

        st.plotly_chart(fig)

st.subheader("💡 My Signals (Public View)")
r = httpx.get(f"{API_URL}/signals")
sig = pd.DataFrame(r.json())
if not sig.empty:
    st.dataframe(sig[["ticker", "action", "confidence", "timestamp"]])
else:
    st.write("No signals yet.")
