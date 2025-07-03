import yfinance as yf

class OptionsAnalyzer:
    def __init__(self):
        pass

    def get_recommendations(self, symbol):
        ticker = yf.Ticker(symbol)
        expirations = ticker.options

        # For simplicity, take the nearest expiration
        if not expirations:
            return []
        nearest_expiry = expirations[0]
        opt_chain = ticker.option_chain(nearest_expiry)
        calls = opt_chain.calls

        # Rank by highest open interest
        calls = calls.sort_values("openInterest", ascending=False)

        top_calls = calls.head(5)
        recommendations = []
        for _, row in top_calls.iterrows():
            recommendations.append({
                "contract": f"{symbol} {row['strike']}C exp {nearest_expiry}",
                "score": float(row["openInterest"])
            })
        return recommendations
