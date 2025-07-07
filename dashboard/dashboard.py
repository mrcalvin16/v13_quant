import streamlit as st
import pandas as pd
import requests
from datetime import datetime

API_BASE = "https://v13-quant.onrender.com"

# Tabs in sidebar
tabs = st.sidebar.radio(
    "Go to",
    [
        "Buy These Now",
        "Watchlist",
        "Ticker Search",
        "Pump & Dump Alerts",
        "Penny Stocks",
        "Earnings Calendar",
        "Historic Data",
        "Admin Dashboard"
    ]
)

# ---- LOAD TICKERS ----
@st.cache_data
def get_tickers():
    try:
        return requests.get(f"{API_BASE}/tickers").json()
    except Exception:
        return []
tickers = get_tickers()

# ---- BUY THESE NOW ----
if tabs == "Buy These Now":
    st.title("🔥 Buy These Now!")
    st.write("AI-Recommended Stocks to Buy Right Now.")
    try:
        top = requests.get(f"{API_BASE}/recommendations/top").json()
        df = pd.DataFrame(top)
        st.dataframe(df[["ticker", "combined_score", "pred_price"]])
        st.bar_chart(df.set_index("ticker")["combined_score"])
    except Exception as e:
        st.error(f"Error loading recommendations: {e}")

# ---- WATCHLIST ----
elif tabs == "Watchlist":
    st.title("👀 My Watchlist")
    st.write("Save your favorite stocks here for quick access.")
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    add_ticker = st.selectbox("Add ticker to Watchlist", [""] + tickers)
    if st.button("Add to Watchlist") and add_ticker and add_ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(add_ticker)
    remove_ticker = st.selectbox("Remove ticker from Watchlist", [""] + st.session_state.watchlist)
    if st.button("Remove from Watchlist") and remove_ticker in st.session_state.watchlist:
        st.session_state.watchlist.remove(remove_ticker)
    st.write("**Your Watchlist:**")
    for ticker in st.session_state.watchlist:
        st.write(f"- {ticker}")

# ---- TICKER SEARCH ----
elif tabs == "Ticker Search":
    st.title("🔍 Ticker Search")
    ticker = st.selectbox("Choose a Ticker", tickers)
    if ticker:
        try:
            res = requests.get(f"{API_BASE}/recommendation/{ticker}").json()
            st.json(res)
            st.write("Combined Score:", res.get("combined_score"))
            st.write("Predicted Price:", res.get("pred_price"))
        except Exception as e:
            st.error(f"Error: {e}")

# ---- PUMP & DUMP ALERTS ----
elif tabs == "Pump & Dump Alerts":
    st.title("🚨 Pump & Dump Radar")
    try:
        signals = requests.get(f"{API_BASE}/signals").json()
        df = pd.DataFrame(signals)
        if not df.empty:
            pump_df = df[(df["confidence"] > 0.85) | (df.get("combined_score", pd.Series([0])) > 0.8)]
            st.write("⚡️ Potential Pump & Dumps (high risk, high reward):")
            st.dataframe(pump_df[["ticker", "action", "confidence", "combined_score", "timestamp"]])
        else:
            st.info("No suspicious activity found.")
    except Exception as e:
        st.error(f"Error loading signals: {e}")

# ---- PENNY STOCKS RADAR ----
elif tabs == "Penny Stocks":
    st.title("💸 Penny Stocks Radar")
    penny_list = []
    for ticker in tickers[:100]:  # Limit for demo
        try:
            res = requests.get(f"{API_BASE}/recommendation/{ticker}").json()
            price = float(res.get("pred_price", 0))
            if 0 < price <= 5:
                penny_list.append({
                    "Ticker": ticker,
                    "Predicted Price": price,
                    "Score": res.get("combined_score"),
                })
        except Exception:
            pass
    penny_df = pd.DataFrame(penny_list)
    if not penny_df.empty:
        st.dataframe(penny_df)
    else:
        st.info("No penny stocks detected in top 100 tickers right now.")

# ---- EARNINGS CALENDAR ----
elif tabs == "Earnings Calendar":
    st.title("📅 Earnings Calendar")
    ticker = st.selectbox("Choose Ticker for Earnings", tickers)
    if ticker:
        try:
            res = requests.get(f"{API_BASE}/earnings/{ticker}").json()
            st.write(f"Next earnings date for {ticker}: {res.get('next_earnings')}")
        except Exception as e:
            st.error(f"Error loading earnings: {e}")

# ---- HISTORIC DATA ----
elif tabs == "Historic Data":
    st.title("📈 Historic Data")
    ticker = st.selectbox("Choose Ticker for Historic Data", tickers)
    if ticker:
        try:
            hist = requests.get(f"{API_BASE}/ticker/{ticker}/history").json()
            df = pd.DataFrame(hist)
            st.line_chart(df.set_index("date")["close"])
        except Exception as e:
            st.error(f"Error loading historic data: {e}")

# ---- ADMIN DASHBOARD ----
elif tabs == "Admin Dashboard":
    st.title("🛠️ Admin Dashboard")
    st.write("Monitor AI performance, model updates, and logs here.")
    try:
        logs = requests.get(f"{API_BASE}/admin/logs").json()
        st.json(logs)
    except Exception as e:
        st.warning("No logs found or admin endpoint not implemented.")
