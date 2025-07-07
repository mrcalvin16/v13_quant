from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import os
from supabase import create_client
from pydantic import BaseModel

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# UTILITIES
# -------------------------------

class WatchlistItem(BaseModel):
    ticker: str

def load_tickers():
    try:
        df = pd.read_csv("nyse-listed.csv")
        return df["Symbol"].tolist()
    except:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]

tickers = load_tickers()

# -------------------------------
# CORE LOGIC FUNCTIONS
# -------------------------------

def simulate_model(ticker):
    price = yf.Ticker(ticker).history(period="5d")["Close"].iloc[-1]
    predicted = price * 1.05
    return {
        "ticker": ticker,
        "current_price": round(price, 2),
        "predicted_price": round(predicted, 2),
        "action": "buy",
        "confidence": "high",
        "timestamp": str(datetime.utcnow())
    }

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
            actual_price = float(df['Close'][-1])
            predicted = entry["predicted_price"]
            action = entry.get("action", "buy")
            win = "win" if (actual_price >= predicted and action == "buy") or (actual_price <= predicted and action == "sell") else "loss"
            supabase.table("prediction_log").update({
                "actual_price": actual_price,
                "outcome": win
            }).eq("id", entry["id"]).execute()
        except Exception as e:
            print(f"Backfill error for {ticker}: {e}")

# -------------------------------
# ENDPOINTS
# -------------------------------

@app.get("/recommendations/top")
def top_recommendations():
    results = []
    for ticker in tickers[:10]:
        data = simulate_model(ticker)
        supabase.table("prediction_log").insert(data).execute()
        results.append(data)
    return results

@app.get("/options/top")
def top_options():
    return [{"ticker": t, "type": "call", "target": 1.1} for t in tickers[:10]]

@app.get("/historic")
def historic_data():
    result = []
    for t in tickers[:5]:
        df = yf.Ticker(t).history(period="1mo")["Close"]
        result.append({
            "ticker": t,
            "history": df.tail(5).to_dict()
        })
    return result

@app.get("/earnings")
def earnings_calendar():
    result = []
    for t in tickers[:10]:
        try:
            cal = yf.Ticker(t).calendar
            result.append({"ticker": t, "calendar": cal.to_dict() if hasattr(cal, 'to_dict') else str(cal)})
        except:
            continue
    return result

@app.get("/pumps")
def pump_and_dumps():
    return [{"ticker": t, "spike": "30% in 2d"} for t in tickers[-5:]]

@app.get("/admin/metrics")
def metrics():
    update_prediction_outcomes()
    logs = supabase.table("prediction_log").select("*").execute().data
    return logs

@app.get("/search")
def search_ticker(q: str):
    matches = [t for t in tickers if q.upper() in t]
    return matches[:10]

@app.post("/watchlist")
def add_watchlist(item: WatchlistItem):
    supabase.table("watchlist").insert({"ticker": item.ticker, "added": str(datetime.utcnow())}).execute()
    return {"status": "added"}

@app.get("/watchlist")
def get_watchlist():
    return supabase.table("watchlist").select("*").execute().data

@app.get("/buynow")
def quick_wins():
    data = []
    for t in tickers[:10]:
        model = simulate_model(t)
        if model["predicted_price"] > model["current_price"] * 1.05:
            data.append(model)
    return data
