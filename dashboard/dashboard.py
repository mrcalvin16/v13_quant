import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go

API_BASE = "https://v13-quant.onrender.com"

st.set_page_config(
    page_title="Oracle Black AI: Buy These Now",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("## 💪 Oracle Black AI: Buy These Now")
st.markdown(
    """
    Welcome to your AI-powered stock picks dashboard.  
    Get today's highest-conviction stocks and options, all signals ranked for actionable gains.
    """
)

# --- Fetch top recommendations ---
@st.cache_data(ttl=180)
def fetch_recommendations():
    try:
        r = requests.get(f"{API_BASE}/recommendations/top", timeout=12)
        r.raise_for_status()
        data = r.json()
        return data.get("winning", []), data.get("log", [])
    except Exception as e:
        st.error(f"Error fetching signals: {e}")
        return [], []

winning, log = fetch_recommendations()

# --- Display BUY signals ---
if not winning:
    st.info("🚦 No winning signals available at the moment.")
else:
    st.markdown("### 📈 These Stocks Are A Win: Buy Now")
    df = pd.DataFrame(winning)
    df_display = df[["symbol", "score", "reason"]].sort_values("score", ascending=False)
    st.dataframe(df_display, height=350, use_container_width=True)
    
    st.markdown("#### 📊 Signal Scores Chart")
    chart = go.Figure(data=[
        go.Bar(
            x=df_display["symbol"],
            y=df_display["score"],
            text=df_display["reason"],
            hoverinfo="text+y"
        )
    ])
    chart.update_layout(
        xaxis_title="Ticker",
        yaxis_title="AI Signal Score",
        showlegend=False,
        margin=dict(t=30, b=30)
    )
    st.plotly_chart(chart, use_container_width=True)

# --- Options/Earnings Data ---
st.divider()
st.markdown("## Options Data (Experimental)")
try:
    # Get tickers list
    tickers_resp = requests.get(f"{API_BASE}/tickers", timeout=8)
    tickers_resp.raise_for_status()
    tickers = tickers_resp.json().get("tickers", [])
except Exception:
    tickers = []

chosen = st.selectbox("Choose a stock for live options data:", tickers) if tickers else st.selectbox("Choose a stock for live options data:", ["No options to select"])
col1, col2 = st.columns(2)

if chosen and chosen != "No options to select":
    with col1:
        if st.button("Load Options Chain"):
            try:
                opt = requests.get(f"{API_BASE}/options/{chosen}", timeout=12).json()
                if not opt.get("options"):
                    st.warning("No options data available.")
                else:
                    opt_df = pd.DataFrame(opt["options"])
                    st.dataframe(opt_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading options: {e}")

    with col2:
        if st.button("Get Earnings Calendar"):
            try:
                cal = requests.get(f"{API_BASE}/earnings/{chosen}", timeout=8).json()
                if not cal.get("calendar"):
                    st.warning("No earnings calendar available.")
                else:
                    cal_df = pd.DataFrame(cal["calendar"])
                    st.dataframe(cal_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading earnings calendar: {e}")

st.caption("Oracle Black AI ULTRA • All picks are AI-generated and do not constitute financial advice.")

# --- Optional: Debug/log section for admin only ---
if st.sidebar.button("Show Prediction Log"):
    if log:
        st.markdown("### 🔍 Prediction Log")
        st.json(log)
    else:
        st.info("No prediction logs available.")
