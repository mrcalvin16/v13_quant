import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objs as go
import streamlit_authenticator as stauth
import yfinance as yf

API_URL = "http://localhost:8000"

# Example credentials
credentials = {
    "usernames": {
        "user1": {
            "email": "user1@example.com",
            "name": "User One",
            "password": stauth.Hasher(["your_password"]).generate()[0]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "cookie_name",
    "signature_key",
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:

    st.sidebar.success(f"Welcome {name}!")

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

    st.subheader("💡 My Signals")
    r = httpx.get(f"{API_URL}/signals", headers={"Authorization": f"Bearer {authenticator.token}"})
    sig = pd.DataFrame(r.json())
    if not sig.empty:
        st.dataframe(sig[["ticker", "action", "confidence", "timestamp"]])
    else:
        st.write("No signals yet.")

else:
    st.warning("Please log in to access the dashboard.")
