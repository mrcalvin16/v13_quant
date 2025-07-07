import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

BACKEND_URL = "https://v13-quant.onrender.com"

st.set_page_config(page_title="V13 Quant Dashboard", layout="wide")

st.sidebar.title("Go to")
tab = st.sidebar.radio("", ["Ticker Search", "Recommendations", "Strategies", "Options & Earnings"])

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button {font-size: 1.15rem;}
    .score-chip {display: inline-block; padding: 0.4em 1em; border-radius: 2em; color: #fff;}
    .score-buy {background: #41b883;}
    .score-hold {background: #f7b32b;}
    .score-sell {background: #e94f37;}
    </style>
""", unsafe_allow_html=True)

def fetch(endpoint, method="get", **kwargs):
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == "get":
            r = requests.get(url, timeout=7)
        elif method == "post":
            r = requests.post(url, **kwargs, timeout=7)
        else:
            return None
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
    return None

if tab == "Ticker Search":
    st.header("🔍 Search Tickers")
    tickers = fetch("/tickers") or []
    default_ticker = tickers[0] if tickers else "AAPL"
    ticker = st.selectbox("Select Ticker", options=tickers or ["AAPL"], index=0)
    col1, col2 = st.columns([1,1])

    with col1:
        if st.button("Get Recommendation"):
            rec = fetch(f"/recommendation/{ticker}")
            if rec:
                st.markdown(f"""
                <h4>{ticker} Recommendation</h4>
                <div>
                <span class="score-chip score-buy">Buy Score: {rec['combined_score']:.2f}</span>
                <span class="score-chip score-hold">Predicted: ${rec['pred_price']:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
                st.write("Scores:")
                st.json(rec)
                # Show a simple bar chart of scores
                scores = {
                    'Prediction': rec['pred_score'],
                    'Pump Score': rec['pump_score'],
                    'Earnings': rec['earnings_score'],
                    'Options': rec['opt_score']
                }
                fig = go.Figure([go.Bar(x=list(scores.keys()), y=list(scores.values()), marker_color="deepskyblue")])
                fig.update_layout(title="Score Breakdown", yaxis=dict(range=[0,1]))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No recommendation found or backend error.")

    with col2:
        if st.button("Save Search"):
            resp = fetch(f"/search-history?ticker={ticker}", method="post")
            st.success("Search saved!" if resp else "Failed to save.")

elif tab == "Recommendations":
    st.header("💡 Top Recommendations")
    data = fetch("/recommendations/top")
    if data and isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        st.dataframe(df.style.background_gradient(cmap="YlGn"), use_container_width=True)
        # Simple scatter of top combined scores
        fig = go.Figure(go.Bar(
            x=df['ticker'] if 'ticker' in df else df['symbol'],
            y=df['combined_score'],
            marker_color=df['combined_score'],
            text=df['combined_score'],
            textposition='auto'
        ))
        fig.update_layout(title="Top Combined Scores", yaxis_title="Score")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recommendations available yet.")

elif tab == "Strategies":
    st.header("🛠️ Strategies")
    strategies = fetch("/strategies")
    if strategies:
        for s in strategies:
            st.subheader(s.get("name"))
            st.caption(s.get("description"))
            tags = s.get("tags", [])
            tag_str = " ".join([f"`{tag}`" for tag in tags])
            st.markdown(f"**Tags:** {tag_str}")
            if st.button(f"Subscribe to {s.get('name')}", key=f"sub_{s['id']}"):
                resp = fetch("/subscribe", method="post", json={"strategy_id": s['id']})
                if resp and resp.get("status") == "subscribed":
                    st.success(f"Subscribed to {s.get('name')}!")
                else:
                    st.error("Failed to subscribe.")
    else:
        st.info("No strategies found.")

elif tab == "Options & Earnings":
    st.header("📅 Options & Earnings")
    tickers = fetch("/tickers") or ["AAPL"]
    ticker = st.selectbox("Select Ticker for Options", options=tickers, index=0)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Options Chain"):
            data = fetch(f"/options/{ticker}")
            if data and isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                st.dataframe(df.head(20), use_container_width=True)
                # Plot option prices vs strike
                if 'strike' in df and 'lastPrice' in df:
                    fig = go.Figure()
                    df_call = df[df['type'] == 'call']
                    df_put = df[df['type'] == 'put']
                    fig.add_trace(go.Scatter(x=df_call['strike'], y=df_call['lastPrice'],
                                             mode='markers+lines', name='Calls', marker_color='green'))
                    fig.add_trace(go.Scatter(x=df_put['strike'], y=df_put['lastPrice'],
                                             mode='markers+lines', name='Puts', marker_color='red'))
                    fig.update_layout(title=f"Options Chain: {ticker}", xaxis_title="Strike", yaxis_title="Last Price")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Failed: Internal Server Error")

    with col2:
        if st.button("Get Earnings Calendar"):
            earnings = fetch(f"/earnings/{ticker}")
            st.write("Earnings Date:", earnings.get("next_earnings", "N/A"))
