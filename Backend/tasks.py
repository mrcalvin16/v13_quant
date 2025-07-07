from backend.main import get_recommendation, send_email
from backend.models import get_prediction_score, get_predicted_price
import pandas as pd
from supabase import create_client
import os

# Load environment variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Load tickers
def load_tickers():
    nyse = pd.read_csv("data/nyse-listed.csv")
    other = pd.read_csv("data/other-listed.csv")
    nyse_symbols = nyse["Symbol"].dropna().unique().tolist()
    other_symbols = other["Symbol"].dropna().unique().tolist()
    return sorted(set(nyse_symbols + other_symbols))

tickers = load_tickers()

# Batch scoring
print(f"Scoring {len(tickers)} tickers...")
for t in tickers:
    try:
        rec = get_recommendation(t)
        supabase.table("recommendations").insert({
            "ticker": t,
            "pred_score": rec["pred_score"],
            "pump_score": rec["pump_score"],
            "earnings_score": rec["earnings_score"],
            "opt_score": rec["opt_score"],
            "combined_score": rec["combined_score"]
        }).execute()
        print(f"✅ Scored {t}: {rec['combined_score']:.2f}")
    except Exception as e:
        print(f"⚠️ Error scoring {t}: {e}")

# Retrieve Top 10 recommendations
res = supabase.table("recommendations")\
    .select("*")\
    .order("combined_score", desc=True)\
    .limit(10)\
    .execute()

top = res.data

# Build email body
body = "🚀 Top 10 Daily Recommendations:\n\n"
for r in top:
    body += (
        f"{r['ticker']} - Combined Score: {r['combined_score']:.2f}\n"
        f"Predictive: {r['pred_score']:.2f}, Pump: {r['pump_score']:.2f}, "
        f"Earnings: {r['earnings_score']:.2f}, Options: {r['opt_score']:.2f}\n\n"
    )

# Send email summary
send_email(
    recipient="you@example.com",
    subject="Daily Top Trading Picks",
    body=body
)

print("✅ Daily email sent.")
