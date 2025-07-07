import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

API_URL = "https://v13-quant.onrender.com"

st.set_page_config(page_title="Oracle Black AI: Buy These Now", layout="wide")

st.title("🦾 Oracle Black AI: Buy These Now")

st.markdown("""
Welcome to your AI-powered stock picks dashboard.  
Get today's highest-conviction stocks and options, all signals ranked for actionable gains.
""")

# --- Fetch top signals ("Buy These Now") ---
def fetch_signals():
    try:
        r = requests.get(f"{API_URL}/recommendations/top")
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"Error fetching signals: {e}")
        return pd.DataFrame()

signals_df = fetch_signals()

if signals_df.empty:
    st.warning("No winning signals available at the moment.")
else:
    st.subheader("🔥 Buy These Now (Top AI Picks)")
    st.dataframe(signals_df[["ticker", "pred_price", "combined_score", "confidence", "price_target", "action"]], use_container_width=True)

    # --- Visual: Bar chart of combined scores ---
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=signals_df["ticker"],
        y=signals_df["combined_score"],
        text=signals_df["confidence"],
        name="Combined Score"
    ))
    fig.update_layout(
        title="AI Combined Scores (Higher = Stronger Buy)",
        xaxis_title="Ticker",
        yaxis_title="Combined Score",
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Visual: Price Targets ---
    st.subheader("Target Prices & Actions")
    for _, row in signals_df.iterrows():
        st.metric(
            label=f"{row['ticker']} ({row['action'].capitalize()})",
            value=f"${row['pred_price']:.2f}",
            delta=f"Target: ${row['price_target']:.2f} | Confidence: {row['confidence']:.2f}"
        )

# --- Options signals ---
st.markdown("---")
st.subheader("Options Data (Experimental)")

selected_ticker = st.selectbox("Choose a stock for live options data:", signals_df["ticker"].unique() if not signals_df.empty else [])

if selected_ticker:
    @st.cache_data
    def fetch_options(ticker):
        try:
            r = requests.get(f"{API_URL}/options/{ticker}")
            r.raise_for_status()
            return pd.DataFrame(r.json())
        except Exception as e:
            st.error(f"Error fetching options: {e}")
            return pd.DataFrame()

    options_df = fetch_options(selected_ticker)
    if not options_df.empty:
        st.dataframe(options_df[["expiration", "strike", "type", "lastPrice", "impliedVolatility", "volume", "openInterest"]].head(25), use_container_width=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=options_df["strike"],
            y=options_df["impliedVolatility"],
            mode="markers",
            marker=dict(size=8, opacity=0.7),
            name="IV"
        ))
        fig2.update_layout(
            title=f"Options IV Curve for {selected_ticker}",
            xaxis_title="Strike",
            yaxis_title="Implied Volatility"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No options data for this ticker yet.")

st.caption("Oracle Black AI ULTRA • All picks are AI-generated and do not constitute financial advice.")
