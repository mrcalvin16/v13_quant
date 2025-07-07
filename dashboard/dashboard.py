import streamlit as st
import requests

API_URL = "https://v13-quant.onrender.com"  # Change to your FastAPI URL

st.set_page_config("V13 Quant Dashboard", layout="wide")
st.title("📊 V13 Quant Dashboard")

# ------- 1. Sidebar Navigation -------
tabs = [
    "Ticker Search",
    "Recommendations",
    "Strategies",
    "Options & Earnings"
]
tab = st.sidebar.radio("Go to", tabs)

# ------- 2. Caching API Calls -------
@st.cache_data(show_spinner=False)
def fetch_tickers():
    try:
        res = requests.get(f"{API_URL}/tickers")
        res.raise_for_status()
        return sorted(res.json())
    except Exception as e:
        st.error(f"Failed to fetch tickers: {e}")
        return []

@st.cache_data(show_spinner=False)
def fetch_strategies():
    try:
        res = requests.get(f"{API_URL}/strategies")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Failed to fetch strategies: {e}")
        return []

@st.cache_data(show_spinner=False)
def fetch_recommendations():
    try:
        res = requests.get(f"{API_URL}/recommendations/top")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Failed to fetch recommendations: {e}")
        return []

# ------- 3. Ticker Search Tab -------
if tab == "Ticker Search":
    st.header("🔍 Search Tickers")
    tickers = fetch_tickers()
    ticker = st.selectbox("Select Ticker", tickers, index=0 if tickers else None)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get Recommendation"):
            try:
                r = requests.get(f"{API_URL}/recommendation/{ticker}")
                if r.ok:
                    rec = r.json()
                    st.json(rec)
                else:
                    st.error(f"Error: {r.text}")
            except Exception as e:
                st.error(f"Failed: {e}")
    with col2:
        if st.button("Save Search"):
            try:
                r = requests.post(f"{API_URL}/search-history", params={"ticker": ticker})
                if r.ok:
                    st.success("Saved search.")
                else:
                    st.error(f"Save failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# ------- 4. Recommendations Tab -------
elif tab == "Recommendations":
    st.header("💡 Top Recommendations")
    data = fetch_recommendations()
    if not data:
        st.info("No recommendations available.")
    else:
        st.table(data)

# ------- 5. Strategies Tab -------
elif tab == "Strategies":
    st.header("🚀 Strategies")
    strategies = fetch_strategies()
    if not strategies:
        st.warning("No strategies found.")
    else:
        for s in strategies:
            st.subheader(s["name"])
            st.write(s["description"])
            tags = s.get("tags")
            if tags:
                st.write(f"**Tags:** {tags}")
            if st.button(f"Subscribe to {s['name']}", key=f"subscribe_{s['id']}"):
                try:
                    r = requests.post(f"{API_URL}/subscribe", json={"strategy_id": s["id"]})
                    if r.ok:
                        st.success(f"Subscribed to {s['name']}!")
                    else:
                        st.error(f"Failed to subscribe: {r.text}")
                except Exception as e:
                    st.error(f"Failed to subscribe: {e}")

# ------- 6. Options & Earnings Tab -------
elif tab == "Options & Earnings":
    st.header("🗓️ Options & Earnings")
    tickers = fetch_tickers()
    ticker = st.selectbox("Select Ticker for Options", tickers, index=0 if tickers else None, key="options_ticker")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load Options Chain"):
            try:
                r = requests.get(f"{API_URL}/options/{ticker}")
                if r.ok:
                    options = r.json()
                    st.dataframe(options)
                else:
                    st.error(f"Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        if st.button("Get Earnings Calendar"):
            try:
                r = requests.get(f"{API_URL}/earnings/{ticker}")
                if r.ok:
                    earnings = r.json()
                    st.json(earnings)
                else:
                    st.error(f"Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")
