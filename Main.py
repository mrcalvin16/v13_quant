import streamlit as st
from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from simulation.simulator import Simulator
from prediction.options_scanner import OptionsAnalyzer

# Initialize models
ml_model = MLEnsemble()
rl_agent = RLAgent()
ensemble = EnsembleManager(
    ml_model=ml_model,
    rl_model=rl_agent,
    weight_rl=0.4
)

# Initialize simulator with example returns
simulator = Simulator(returns=[0.01, -0.02, 0.015])

# Initialize options analyzer
options_analyzer = OptionsAnalyzer()

# Streamlit UI
st.set_page_config(page_title="📊 V13 Quant System")

st.title("🚀 V13 Quant System")
st.success("✅ App loaded successfully!")

# Show module status
st.subheader("Modules Status")
st.write("- ML Prediction Module: Ready")
st.write("- RL Agent Module: Ready")
st.write("- Options Analyzer Module: Ready (analysis only)")
st.write("- Simulator Module: Ready")

# Example performance metrics
st.subheader("Example Performance Metrics")
metrics = {
    "Sharpe Ratio": 1.42,
    "Win Rate": "62%",
    "Max Drawdown": "-12%",
}
st.table(metrics.items())

# Options Analyzer UI (God Mode)
st.subheader("Options Analyzer (God Mode)")

symbol = st.text_input("Ticker Symbol", value="AAPL")

col1, col2 = st.columns(2)
min_iv = col1.slider("Minimum Implied Volatility", 0.0, 1.0, 0.2)
max_iv = col2.slider("Maximum Implied Volatility", 0.0, 1.0, 0.6)

min_oi = st.number_input("Minimum Open Interest", value=500)
min_volume = st.number_input("Minimum Volume", value=250)
max_spread = st.number_input("Maximum Spread ($)", value=0.25)

st.markdown("### Scoring Weights")
scoring_weights = {
    "liquidity": st.slider("Liquidity Weight", 0, 10, 1),
    "iv": st.slider("IV Penalty Weight", 0, 10, 1),
    "volume": st.slider("Volume Weight", 0, 10, 1),
    "spread": st.slider("Spread Penalty Weight", 0, 10, 1)
}

if st.button("Get Options Recommendations"):
    with st.spinner("Analyzing options chain..."):
        recs = options_analyzer.get_recommendations(
            symbol,
            min_oi=min_oi,
            min_volume=min_volume,
            min_iv=min_iv,
            max_iv=max_iv,
            max_spread=max_spread,
            scoring_weights=scoring_weights
        )

    if recs:
        st.write(f"Top options contracts for {symbol}:")
        for r in recs:
            st.write(
                f"- **{r['contract']}** | "
                f"Strike: {r['strike']} | "
                f"IV: {r['iv']:.2f} | "
                f"OI: {r['oi']} | "
                f"Volume: {r['volume']} | "
                f"Spread: {r['spread']:.2f} | "
                f"Score: {r['score']:.1f}"
            )
    else:
        st.warning("No options met your criteria.")

# ML prediction example
st.subheader("ML Blended Prediction")
ml_input = [0.2, 0.3, -0.1]
rl_obs = [0.05, 0.02]
prediction = ensemble.predict(ml_input, rl_obs)
st.write(f"Blended prediction signal: {prediction:.4f}")

# Show simulated returns chart
st.subheader("Simulation Returns")
st.line_chart(simulator.returns)
