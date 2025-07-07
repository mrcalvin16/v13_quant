import streamlit as st
import requests
import pandas as pd

# 🟢 Set your backend API base URL
API_URL = "https://v13-quant.onrender.com"

st.set_page_config(page_title="📈 V13 Quant Dashboard", layout="wide")

st.title("📈 V13 Quant Dashboard")

# Load tickers
@st.cache_data
def load_tickers():
    r = requests.get(f"{API_URL}/tickers")
    r.raise_for_status()
    return r.json()

# Load strategies
@st.cache_data
def load_strategies():
    r = requests.get(f"{API_URL}/strategies")
    r.raise_for_status()
    return r.json()

# Main navigation
tabs = st.tabs(["🔍 Ticker Search", "💡 Recommendations", "🛠 Strategies", "📈 Options & Earnings"])

# Ticker Search Tab
with tabs[0]:
    st.header("🔍 Search Tickers")
    tickers = load_tickers()
    ticker = st.selectbox("Select Ticker", sorted(tickers))
    if st.button("Get Recommendation"):
        r = requests.get(f"{API_URL}/recommendation/{ticker}")
        if r.ok:
            data = r.json()
            st.json(data)
        else:
            st.error(f"Error: {r.status_code}\n{r.text}")

    if st.button("Save Search"):
        r = requests.post(f"{API_URL}/search-history", params={"ticker": ticker})
        if r.ok:
            st.success("Search saved.")
        else:
            st.error(f"Error: {r.status_code}\n{r.text}")

# Recommendations Tab
with tabs[1]:
    st.header("💡 Top Recommendations")
    r = requests.get(f"{API_URL}/recommendations/top")
    if r.ok:
        data = pd.DataFrame(r.json())
        st.dataframe(data)
    else:
        st.error(f"Error: {r.status_code}\n{r.text}")

# Strategies Tab
with tabs[2]:
    st.header("🛠 Strategies")
    strategies = load_strategies()
    if strategies:
        for s in strategies:
            st.subheader(s["name"])
            st.write(s["description"])
            if st.button(f"Subscribe to {s['name']}"):
                r = requests.post(f"{API_URL}/subscribe", json={"strategy_id": s["id"]})
                if r.ok:
                    st.success("Subscribed.")
                else:
                    st.error(f"Error: {r.status_code}\n{r.text}")
    else:
        st.info("No strategies found.")

    st.divider()
    st.subheader("Publish Signal")
    with st.form("signal_form"):
        strategy_id = st.text_input("Strategy ID")
        ticker = st.text_input("Ticker")
        action = st.selectbox("Action", ["buy", "sell"])
        price_target = st.number_input("Price Target", min_value=0.0)
        confidence = st.slider("Confidence", 0.0, 1.0, 0.5)
        submitted = st.form_submit_button("Publish")
        if submitted:
            payload = {
                "strategy_id": strategy_id,
                "ticker": ticker,
                "action": action,
                "price_target": price_target,
                "confidence": confidence
            }
            r = requests.post(f"{API_URL}/signals", json=payload)
            if r.ok:
                st.success("Signal published.")
            else:
                st.error(f"Error: {r.status_code}\n{r.text}")

# Options & Earnings Tab
with tabs[3]:
    st.header("📈 Options & Earnings")
    ticker2 = st.selectbox("Select Ticker for Options", sorted(tickers), key="opt")
    if st.button("Load Options Chain"):
        r = requests.get(f"{API_URL}/options/{ticker2}")
        if r.ok:
            data = pd.DataFrame(r.json())
            st.dataframe(data)
        else:
            st.error(f"Error: {r.status_code}\n{r.text}")
    if st.button("Get Earnings Calendar"):
        r = requests.get(f"{API_URL}/earnings/{ticker2}")
        if r.ok:
            st.json(r.json())
        else:
            st.error(f"Error: {r.status_code}\n{r.text}")

st.caption("V13 Quant Platform © 2025")
