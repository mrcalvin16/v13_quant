import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import yfinance as yf
from supabase import create_client
from datetime import datetime, timedelta

# --- Supabase Connection ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load or define your tickers (replace with your own logic/file) ---
def load_tickers():
    # For example, load from CSV, or fallback to a sample list
    try:
        nyse = pd.read_csv("nyse-listed.csv")
        return list(nyse['Symbol'])
    except Exception:
        # Fallback
        return ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA"]

tickers = load_tickers()

# --- Helper: Get last closing price ---
def get_latest_close(symbol):
    try:
        hist = yf.Ticker(symbol).history(period="1d")
        if hist.empty:
            print(f"Skipping {symbol}: No price data (may be delisted)")
            return None
        return float(hist['Close'].iloc[-1])
    except Exception as e:
        print(f"Error with {symbol}: {e}")
        return None

# --- Recommendation logic (dummy) ---
def get_stock_recommendations(n=5):
    recs = []
    for symbol in tickers[:n]:
        price = get_latest_close(symbol)
        if price is None:
            continue
        # Add more logic here (e.g., AI predictions, metrics, etc.)
        recs.append({
            "symbol": symbol,
            "price": price,
            "action": "buy",  # Placeholder logic
            "confidence": 0.92  # Dummy value
        })
    return recs

# --- Prediction log update ---
def update_prediction_outcomes():
    logs = supabase.table("prediction_log").select("*").is_("actual_price", None).execute().data
    for entry in logs:
        ticker = entry["ticker"]
        pred_time = datetime.fromisoformat(entry["timestamp"])
        check_time = pred_time + timedelta(days=2)
        if datetime.utcnow() < check_time:
            continue

        try:
            tk = yf.Ticker(ticker)
            df = tk.history(start=pred_time.date(), end=check_time.date())
            if len(df) < 2:
                continue
            actual_price = float(df['Close'].iloc[-1])
            predicted = entry["predicted_price"]
            action = entry.get("action", "buy")
            win = "win" if (actual_price >= predicted and action == "buy") or (actual_price <= predicted and action == "sell") else "loss"
            supabase.table("prediction_log").update({
                "actual_price": actual_price,
                "outcome": win
            }).eq("id", entry["id"]).execute()
        except Exception as e:
            print(f"Backfill error for {ticker}: {e}")

# --- API Endpoints ---

@app.get("/tickers")
def api_tickers():
    return {"tickers": tickers}

@app.get("/recommendations/top")
def top_recommendations(n: int = 5):
    recs = get_stock_recommendations(n)
    if not recs:
        raise HTTPException(status_code=404, detail="No recommendations available.")
    return {"recommendations": recs}

@app.get("/admin/metrics")
def metrics():
    # This could be improved—pull real stats from logs table
    update_prediction_outcomes()
    log_count = supabase.table("prediction_log").select("*").execute().data
    win_count = sum(1 for x in log_count if x.get("outcome") == "win")
    loss_count = sum(1 for x in log_count if x.get("outcome") == "loss")
    return {
        "total_predictions": len(log_count),
        "wins": win_count,
        "losses": loss_count,
        "win_rate": round(100 * win_count / max(1, (win_count+loss_count)), 2)
    }

@app.get("/admin/logs")
def logs():
    # Returns latest logs (could be filtered, paginated, etc.)
    data = supabase.table("prediction_log").select("*").order("timestamp", desc=True).limit(50).execute().data
    return {"logs": data}

# Add more endpoints as needed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
