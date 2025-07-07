import streamlit as st
import pandas as pd
import requests
import plotly.express as px

BACKEND_URL = "https://v13-quant.onrender.com"

st.set_page_config(layout="wide")
st.title("Oracle Black ULTRA Dashboard")

tabs = st.tabs(["Buy Now", "Options", "Earnings", "Historic Data", "Search", "Pump & Dumps", "Admin"])

with tabs[0]:
    st.header("Buy These NOW (Predictions)")
    res = requests.get(f"{BACKEND_URL}/recommendations/top")
    if res.ok:
        top = pd.DataFrame(res.json())
        st.dataframe(top)
        if not top.empty:
            st.write("### Highest Confidence Buy Now:")
            st.write(top[["ticker", "combined_score", "predicted_price"]].head(5))
        fig = px.bar(top, x="ticker", y="combined_score", title="Top Picks")
        st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.header("Options Chains")
    ticker = st.text_input("Ticker for options", "")
    if ticker:
        res = requests.get(f"{BACKEND_URL}/options/{ticker}")
        if res.ok:
            df = pd.DataFrame(res.json())
            st.dataframe(df)
        else:
            st.warning("No options found.")

with tabs[2]:
    st.header("Upcoming Earnings")
    ticker = st.text_input("Ticker for earnings", "")
    if ticker:
        res = requests.get(f"{BACKEND_URL}/earnings/{ticker}")
        st.write(res.json())

with tabs[3]:
    st.header("Historic Data")
    ticker = st.text_input("Ticker for history", "")
    if ticker:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        df = tk.history(period="1y")
        st.line_chart(df["Close"])

with tabs[4]:
    st.header("Search Stocks")
    tickers = requests.get(f"{BACKEND_URL}/tickers").json()
    search = st.text_input("Search by symbol")
    if search:
        result = [t for t in tickers if search.upper() in t]
        st.write(result)

with tabs[5]:
    st.header("Pump & Dumps / Penny Stocks Detector")
    if st.button("Scan for pump & dumps / penny stocks"):
        flagged = requests.get(f"{BACKEND_URL}/pumpdumps").json()
        st.dataframe(pd.DataFrame(flagged))
        st.write(f"Total flagged: {len(flagged)}")

with tabs[6]:
    st.header("Admin: Logs, Metrics, Training")
    metrics = requests.get(f"{BACKEND_URL}/admin/metrics").json()
    st.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.2f}%")
    st.metric("Avg. Confidence", f"{metrics.get('avg_confidence', 0):.2f}")
    st.metric("Flagged", metrics.get("flagged_count", 0))
    st.write("Current Weights:", metrics.get("weights"))
    logs = requests.get(f"{BACKEND_URL}/admin/logs").json()
    st.write("Recent Events:")
    st.dataframe(pd.DataFrame(logs))
    bad_id = st.number_input("Flag bad prediction by ID", min_value=0, step=1)
    if st.button("Flag"):
        resp = requests.post(f"{BACKEND_URL}/admin/flag", json={"prediction_id": bad_id})
        st.success(f"Flagged {bad_id}: {resp.text}")

st.info("Oracle Black ULTRA - Live, Self-Learning, Pump & Dump-Aware Prediction & Monitoring")
