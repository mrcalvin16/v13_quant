import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

BASE_URL = "https://v13-quant.onrender.com"

st.set_page_config(page_title="Oracle Black ULTRA", layout="wide")
st.title("🧠 Oracle Black ULTRA Dashboard")

tabs = st.tabs([
    "🔮 Buy Now",
    "📈 Historic Data",
    "💰 Earnings",
    "🚨 Pump & Dump",
    "👁 Watchlist",
    "📊 Admin Metrics",
    "🔎 Search"
])

with tabs[0]:
    st.header("🔥 Quick Win Picks")
    resp = requests.get(f"{BASE_URL}/buynow")
    if resp.ok:
        df = pd.DataFrame(resp.json())
        st.dataframe(df)
        for row in df.itertuples():
            fig = go.Figure(data=go.Candlestick(
                x=[row.ticker],
                open=[row.open],
                high=[row.high],
                low=[row.low],
                close=[row.predicted_price]
            ))
            fig.update_layout(title=f"{row.ticker} Forecast", xaxis_title="Symbol", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.header("📜 Historical Trends")
    ticker = st.text_input("Enter Symbol", "AAPL")
    if st.button("Get Historical"):
        resp = requests.get(f"{BASE_URL}/historic?ticker={ticker}")
        if resp.ok:
            hist = pd.DataFrame(resp.json())
            st.line_chart(hist.set_index("date")[["close"]])

with tabs[2]:
    st.header("📆 Earnings Reports")
    resp = requests.get(f"{BASE_URL}/earnings")
    if resp.ok:
        df = pd.DataFrame(resp.json())
        st.dataframe(df)

with tabs[3]:
    st.header("⚠️ Pump & Dump Radar")
    resp = requests.get(f"{BASE_URL}/pumps")
    if resp.ok:
        df = pd.DataFrame(resp.json())
        st.dataframe(df)

with tabs[4]:
    st.header("👁 Watchlist Tracker")
    watch_symbol = st.text_input("Add Ticker to Watchlist")
    if st.button("Add to Watchlist"):
        requests.post(f"{BASE_URL}/watchlist", json={"ticker": watch_symbol})
    resp = requests.get(f"{BASE_URL}/watchlist")
    if resp.ok:
        df = pd.DataFrame(resp.json())
        st.dataframe(df)

with tabs[5]:
    st.header("📊 Admin Metrics / Learning")
    resp = requests.get(f"{BASE_URL}/admin/metrics")
    if resp.ok:
        data = resp.json()
        st.metric("Total Predictions", data.get("total_predictions", 0))
        st.metric("Win Rate", f"{data.get('win_rate', 0):.2%}")
        st.metric("Losses", data.get("losses", 0))

with tabs[6]:
    st.header("🔎 Ticker Search")
    search_query = st.text_input("Search Symbol")
    if st.button("Search"):
        resp = requests.get(f"{BASE_URL}/search?ticker={search_query}")
        if resp.ok:
            result = pd.DataFrame(resp.json())
            st.dataframe(result)
