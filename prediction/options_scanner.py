import yfinance as yf

class OptionsAnalyzer:
    def get_recommendations(
        self, symbol, min_oi=100, min_volume=50,
        min_iv=0.2, max_iv=0.6, max_spread=0.25, scoring_weights=None
    ):
        try:
            ticker = yf.Ticker(symbol)
            options_dates = ticker.options
            if not options_dates:
                return []

            chain = ticker.option_chain(options_dates[0])
            calls = chain.calls

            recommendations = []
            for _, row in calls.iterrows():
                if (
                    row["openInterest"] < min_oi
                    or row["volume"] < min_volume
                    or row["impliedVolatility"] < min_iv
                    or row["impliedVolatility"] > max_iv
                    or row["ask"] - row["bid"] > max_spread
                ):
                    continue

                liquidity = row["openInterest"] + row["volume"]
                spread = row["ask"] - row["bid"]
                iv = row["impliedVolatility"]

                weights = scoring_weights or {
                    "liquidity": 1.0,
                    "iv": 1.0,
                    "volume": 1.0,
                    "spread": 1.0
                }
                score = (
                    weights["liquidity"] * liquidity
                    - weights["iv"] * iv * 100
                    + weights["volume"] * row["volume"]
                    - weights["spread"] * spread * 100
                )

                recommendations.append({
                    "contract": row["contractSymbol"],
                    "strike": row["strike"],
                    "iv": iv,
                    "oi": row["openInterest"],
                    "volume": row["volume"],
                    "spread": spread,
                    "score": score
                })

            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:5]

        except Exception as e:
            return [{"error": str(e)}]
