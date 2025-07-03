import yfinance as yf

class OptionsAnalyzer:
    def __init__(self):
        pass

    def get_recommendations(
        self, symbol,
        min_oi=500,
        min_volume=250,
        min_iv=0.2,
        max_iv=0.6,
        max_spread=0.25,
        min_days=7,
        max_days=45,
        min_delta=0.3,
        max_delta=0.7,
        scoring_weights=None
    ):
        ticker = yf.Ticker(symbol)
        expirations = ticker.options

        if not expirations:
            return []

        nearest_expiry = expirations[0]
        opt_chain = ticker.option_chain(nearest_expiry)
        calls = opt_chain.calls

        # Add extra columns (mock delta and spread for illustration)
        calls["delta"] = 0.5  # yfinance doesn't give delta; replace if you have real source
        calls["spread"] = calls["ask"] - calls["bid"]

        # Filter
        calls = calls[
            (calls["openInterest"] >= min_oi) &
            (calls["volume"] >= min_volume) &
            (calls["impliedVolatility"] >= min_iv) &
            (calls["impliedVolatility"] <= max_iv) &
            (calls["spread"] <= max_spread)
        ]

        # Scoring
        if scoring_weights is None:
            scoring_weights = {"liquidity":1, "iv":1, "spread":1, "volume":1}

        calls["score"] = (
            scoring_weights["liquidity"] * calls["openInterest"] +
            scoring_weights["volume"] * calls["volume"] -
            scoring_weights["iv"] * calls["impliedVolatility"]*100 -
            scoring_weights["spread"] * calls["spread"]*100
        )

        top_calls = calls.sort_values("score", ascending=False).head(10)

        recommendations = []
        for _, row in top_calls.iterrows():
            recommendations.append({
                "contract": f"{symbol} {row['strike']}C exp {nearest_expiry}",
                "strike": float(row["strike"]),
                "iv": float(row["impliedVolatility"]),
                "oi": int(row["openInterest"]),
                "volume": int(row["volume"]),
                "spread": float(row["spread"]),
                "score": float(row["score"])
            })
        return recommendations
