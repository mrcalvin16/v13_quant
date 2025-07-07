import streamlit as st
import pandas as pd
import requests

API_URL = "https://v13-quant.onrender.com"  # <-- Change to your deployed API

st.set_page_config(page_title="Oracle Black AI Dashboard", layout="wide")
st.title("🧠 Oracle Black Quant Dashboard")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    tab = st.radio(
        "Choose a section",
        ("Dashboard", "Recommendations", "Signals", "Strategies", "Options", "Earnings"),
        index=0,
        key="main_nav"
    )
    st.markdown("---")
    st.info("🔄 Powered by Oracle Black AI\n\nUpgrade: Real-time quant + dark web risk signals.")

# Dashboard Tab
if tab == "Dashboard":
    st.header("📊 Quick Glance")
    try:
        r = requests.get(f"{API_URL}/tickers")
        r.raise_for_status()
        tickers = r.json()
        st.success(f"Loaded {len(tickers)} tickers.")
        sample = tickers[:10]
        st.write("Sample tickers:", sample)
    except Exception as e:
        st.error(f"Could not load tickers: {e}")

# Recommendations Tab
elif tab == "Recommendations":
    st.header("💡 Top Recommendations")

    try:
        r = requests.get(f"{API_URL}/recommendations/top")
        r.raise_for_status()
        data = r.json()
        if data and isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            # Check for required columns
            if "combined_score" in df.columns and "ticker" in df.columns:
                buy_now = df[df["combined_score"].fillna(0) >= 0.75].sort_values(by="combined_score", ascending=False)
                if not buy_now.empty:
                    st.success("🔥 **Buy These Now! These stocks are going to be a win:**")
                    for _, row in buy_now.iterrows():
                        st.markdown(
                            f"<span style='font-size:22px;font-weight:bold'>🟢 {row['ticker']}</span> — "
                            f"<span style='font-size:18px;'>Score: <b>{row['combined_score']:.2f}</b></span>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info("No high-confidence 'Buy Now' picks at the moment. Check back soon!")
                st.subheader("Full Recommendations Table")
                st.dataframe(df)
                st.subheader("Combined Score Chart")
                chart_data = df[["ticker", "combined_score"]].set_index("ticker")
                st.bar_chart(chart_data)
            else:
                st.warning("API data is missing expected columns (ticker, combined_score).")
        else:
            st.info("No recommendations found.")
    except Exception as e:
        st.error(f"Error loading recommendations: {e}")

# Signals Tab
elif tab == "Signals":
    st.header("📶 Live Signals")
    try:
        r = requests.get(f"{API_URL}/signals")
        r.raise_for_status()
        data = r.json()
        if data and isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp", ascending=False)
            st.dataframe(df)
        else:
            st.info("No signals available.")
    except Exception as e:
        st.error(f"Error loading signals: {e}")

# Strategies Tab
elif tab == "Strategies":
    st.header("⚙️ Strategies")
    try:
        r = requests.get(f"{API_URL}/strategies")
        r.raise_for_status()
        data = r.json()
        if data and isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.info("No strategies found.")
    except Exception as e:
        st.error(f"Error loading strategies: {e}")

# Options Tab
elif tab == "Options":
    st.header("🪙 Options Data")
    ticker = st.text_input("Enter ticker for options chain:", "AAPL")
    if ticker:
        try:
            r = requests.get(f"{API_URL}/options/{ticker.upper()}")
            r.raise_for_status()
            data = r.json()
            if data and isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                st.dataframe(df)
                # Simple chart: plot Implied Volatility if present
                if "impliedVolatility" in df.columns:
                    st.subheader("Implied Volatility Chart")
                    chart = df.groupby("expiration")["impliedVolatility"].mean()
                    st.line_chart(chart)
            else:
                st.info(f"No options data found for {ticker}.")
        except Exception as e:
            st.error(f"Error loading options for {ticker}: {e}")

# Earnings Tab
elif tab == "Earnings":
    st.header("📅 Earnings Calendar")
    ticker = st.text_input("Enter ticker for earnings date:", "AAPL", key="earnings_ticker")
    if ticker:
        try:
            r = requests.get(f"{API_URL}/earnings/{ticker.upper()}")
            r.raise_for_status()
            data = r.json()
            if "next_earnings" in data and data["next_earnings"]:
                st.success(f"Next earnings date for {ticker.upper()}: {data['next_earnings']}")
            else:
                st.info(f"No upcoming earnings for {ticker.upper()}")
        except Exception as e:
            st.error(f"Error loading earnings for {ticker}: {e}")
