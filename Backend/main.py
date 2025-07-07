from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client
import pandas as pd
import random
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase config
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# Load tickers for search
def load_tickers():
    try:
        nyse = pd.read_csv("nyse-listed.csv")
        nasdaq = pd.read_csv("nasdaq-listed.csv")
        return list(set(nyse['Symbol']).union(set(nasdaq['Symbol'])))
    except Exception as e:
        logger.warning("Could not load tickers:", exc_info=e)
        return ["AAPL", "TSLA", "GOOG", "MSFT", "AMZN", "NVDA", "META", "NFLX", "BABA", "AMD"]

TICKERS = load_tickers()

# Model
class TickerRequest(BaseModel):
    symbol: str

class WatchlistRequest(BaseModel):
    user_id: str
    symbol: str

# Core Logic
def get_top_recommendations(n=10):
    scores = []
    for symbol in random.sample(TICKERS, min(50, len(TICKERS))):
        try:
            data = yf.Ticker(symbol).history(period="5d")
            if len(data) < 5:
                continue
            gain = (data['Close'][-1] - data['Close'][0]) / data['Close'][0]
            score = gain * 100 + random.uniform(-2, 2)
            scores.append({"symbol": symbol, "score": round(score, 2)})
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    top = sorted(scores, key=lambda x: x['score'], reverse=True)[:n]
    return top

def get_options_top(n=10):
    results = []
    for symbol in random.sample(TICKERS, min(30, len(TICKERS))):
        try:
            tk = yf.Ticker(symbol)
            opt_dates = tk.options
            if not opt_dates:
                continue
            calls = tk.option_chain(opt_dates[0]).calls
            top_call = calls.loc[calls['volume'].idxmax()]
            results.append({
                "symbol": symbol,
                "strike": top_call["strike"],
                "volume": int(top_call["volume"]),
                "lastPrice": float(top_call["lastPrice"])
            })
        except Exception:
            continue
    return sorted(results, key=lambda x: x["volume"], reverse=True)[:n]

def detect_penny_stocks(threshold=5.0):
    penny = []
    for sym in random.sample(TICKERS, min(100, len(TICKERS))):
        try:
            price = yf.Ticker(sym).info.get("regularMarketPrice", 100)
            if price is not None and price < threshold:
                penny.append({"symbol": sym, "price": price})
        except:
            continue
    return penny

def log_prediction(symbol, predicted_price, action="buy"):
    now = datetime.utcnow().isoformat()
    supabase.table("prediction_log").insert({
        "ticker": symbol,
        "predicted_price": predicted_price,
        "timestamp": now,
        "action": action
    }).execute()

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
            actual = float(df['Close'][-1])
            predicted = entry["predicted_price"]
            action = entry.get("action", "buy")
            win = "win" if (actual >= predicted and action == "buy") or (actual <= predicted and action == "sell") else "loss"
            supabase.table("prediction_log").update({
                "actual_price": actual,
                "outcome": win
            }).eq("id", entry["id"]).execute()
        except Exception as e:
            logger.warning(f"Backfill error for {ticker}: {e}")

# API ROUTES
@app.get("/recommendations/top")
def recommendations():
    return get_top_recommendations(n=10)

@app.get("/options/top")
def options():
    return get_options_top(n=10)

@app.get("/historic")
def historic():
    data = []
    for sym in random.sample(TICKERS, 5):
        try:
            df = yf.Ticker(sym).history(period="1mo")
            if df.empty: continue
            closes = df['Close'].tolist()
            data.append({"symbol": sym, "history": closes})
        except:
            continue
    return data

@app.get("/earnings")
def earnings():
    results = []
    for sym in random.sample(TICKERS, 20):
        try:
            cal = yf.Ticker(sym).calendar
            if not cal.empty:
                next_earnings = cal.loc["Earnings Date"][0]
                results.append({"symbol": sym, "earnings": str(next_earnings)})
        except:
            continue
    return results

@app.get("/pumps")
def pump_and_dump():
    return detect_penny_stocks()

@app.get("/admin/metrics")
def metrics():
    update_prediction_outcomes()
    logs = supabase.table("prediction_log").select("*").execute().data
    total = len(logs)
    wins = sum(1 for x in logs if x.get("outcome") == "win")
    return {
        "total_predictions": total,
        "wins": wins,
        "accuracy": round((wins / total) * 100, 2) if total else 0
    }

@app.get("/search")
def search(q: str):
    return [s for s in TICKERS if q.upper() in s][:20]

@app.post("/watchlist/add")
def add_watch(req: WatchlistRequest):
    supabase.table("watchlist").insert({
        "user_id": req.user_id,
        "symbol": req.symbol
    }).execute()
    return {"message": "added"}

@app.get("/watchlist/get")
def get_watch(user_id: str):
    results = supabase.table("watchlist").select("*").eq("user_id", user_id).execute().data
    return results

@app.get("/admin")
def admin_view():
    logs = supabase.table("prediction_log").select("*").order("timestamp", desc=True).limit(50).execute().data
    return logs

@app.get("/buynow")
def quick_wins():
    picks = get_top_recommendations(n=20)
    return [x for x in picks if x['score'] > 5][:10]
