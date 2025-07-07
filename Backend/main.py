import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd
import logging

# ------------- Logging Setup -------------
logging.basicConfig(
    filename='app.log', 
    filemode='a', 
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# ------------- App Setup -------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# ------------- Utility Functions -------------
def log_event(event_type, details):
    logger.info(f"{event_type}: {details}")
    try:
        supabase.table("event_log").insert({
            "event_type": event_type,
            "details": str(details),
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Supabase event log error: {e}")

def get_close_price(symbol, days_back=0):
    try:
        data = yf.Ticker(symbol).history(period="5d")
        if len(data) == 0:
            return None
        return float(data['Close'].iloc[-1 - days_back])
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None

def penny_stock_detector(symbol):
    price = get_close_price(symbol)
    return price is not None and price < 5

def is_pump_and_dump(symbol):
    data = yf.Ticker(symbol).history(period="1mo")
    if len(data) < 10:
        return False
    recent = data[-5:]
    prev = data[:-5]
    if prev.empty or recent.empty:
        return False
    recent_vol = recent['Volume'].mean()
    prev_vol = prev['Volume'].mean()
    recent_return = recent['Close'][-1] / recent['Close'][0] - 1
    prev_return = prev['Close'][-1] / prev['Close'][0] - 1
    # Naive pump: spike in volume and return
    return (recent_vol > prev_vol * 2) and (abs(recent_return) > 0.5)

def log_prediction(symbol, prediction, confidence, action, user_id=None):
    try:
        supabase.table("prediction_log").insert({
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": symbol,
            "predicted_price": prediction,
            "confidence": confidence,
            "action": action,
            "user_id": user_id
        }).execute()
        log_event("prediction", {"symbol": symbol, "prediction": prediction, "confidence": confidence, "action": action})
    except Exception as e:
        logger.error(f"Prediction log error: {e}")

def get_stock_recommendations(limit=10):
    # Simulate model predictions for demo, replace with your ML logic
    watch = get_watchlist_symbols()
    symbols = watch if watch else ['AAPL','TSLA','NVDA','MSFT','AMZN']
    results = []
    for symbol in symbols:
        price = get_close_price(symbol)
        if price is None:
            continue
        confidence = 0.7 + 0.2 * (hash(symbol) % 10) / 10
        pred = price * (1 + 0.01 * ((hash(symbol) % 20) - 10))  # Simulated pred
        action = "buy" if pred > price else "hold"
        results.append({
            "symbol": symbol,
            "current_price": price,
            "predicted_price": round(pred, 2),
            "confidence": round(confidence, 2),
            "action": action,
            "buy_now": action == "buy" and confidence > 0.7
        })
    results = sorted(results, key=lambda x: -x["confidence"])
    return results[:limit]

def get_watchlist_symbols():
    try:
        res = supabase.table("watchlist").select("symbol").execute()
        return [r["symbol"] for r in res.data] if res.data else []
    except Exception:
        return []

def add_to_watchlist(symbol, user_id=None):
    try:
        supabase.table("watchlist").insert({
            "symbol": symbol,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
        log_event("watchlist_add", {"symbol": symbol, "user_id": user_id})
        return True
    except Exception as e:
        logger.error(f"Watchlist add error: {e}")
        return False

def remove_from_watchlist(symbol, user_id=None):
    try:
        supabase.table("watchlist").delete().eq("symbol", symbol).execute()
        log_event("watchlist_remove", {"symbol": symbol, "user_id": user_id})
        return True
    except Exception as e:
        logger.error(f"Watchlist remove error: {e}")
        return False

def get_historic_data(symbol, period="1y"):
    try:
        df = yf.Ticker(symbol).history(period=period)
        return df.reset_index().to_dict("records")
    except Exception as e:
        logger.error(f"Historic data error for {symbol}: {e}")
        return []

def search_tickers(query):
    # Simple example: search in watchlist, but you can expand
    all_symbols = get_watchlist_symbols()
    return [s for s in all_symbols if query.lower() in s.lower()]

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
            log_event("prediction_result", {"symbol": ticker, "actual_price": actual_price, "outcome": win})
        except Exception as e:
            logger.error(f"Backfill error for {ticker}: {e}")

# ------------- API ROUTES -------------
@app.get("/recommendations/top")
def top_recommendations():
    recs = get_stock_recommendations()
    log_event("fetch_recommendations", {"count": len(recs)})
    return {"recommendations": recs}

@app.get("/buy_now")
def buy_now():
    recs = get_stock_recommendations()
    buy_now = [r for r in recs if r.get("buy_now")]
    log_event("fetch_buy_now", {"count": len(buy_now)})
    return {"buy_now": buy_now}

@app.get("/historic/{symbol}")
def historic(symbol: str, period: str = Query("1y")):
    data = get_historic_data(symbol, period)
    log_event("fetch_historic", {"symbol": symbol, "count": len(data)})
    return {"symbol": symbol, "history": data}

@app.get("/search")
def search(query: str):
    results = search_tickers(query)
    log_event("search", {"query": query, "results": results})
    return {"results": results}

@app.get("/watchlist")
def watchlist():
    symbols = get_watchlist_symbols()
    log_event("fetch_watchlist", {"count": len(symbols)})
    return {"watchlist": symbols}

@app.post("/watchlist/add")
def add_watch(symbol: str, user_id: str = None):
    ok = add_to_watchlist(symbol, user_id)
    return {"success": ok}

@app.post("/watchlist/remove")
def remove_watch(symbol: str, user_id: str = None):
    ok = remove_from_watchlist(symbol, user_id)
    return {"success": ok}

@app.get("/penny_stocks")
def penny_stocks():
    # In practice, get a wider set of tickers
    symbols = get_watchlist_symbols() or ['AAPL','TSLA','NVDA','MSFT','AMZN']
    pennies = [s for s in symbols if penny_stock_detector(s)]
    log_event("penny_detect", {"count": len(pennies)})
    return {"penny_stocks": pennies}

@app.get("/pump_and_dumps")
def pump_and_dumps():
    symbols = get_watchlist_symbols() or ['AAPL','TSLA','NVDA','MSFT','AMZN']
    pumps = [s for s in symbols if is_pump_and_dump(s)]
    log_event("pump_detect", {"count": len(pumps)})
    return {"pump_and_dumps": pumps}

@app.get("/admin/metrics")
def metrics():
    update_prediction_outcomes()
    # Metrics: Win rate, total predictions, etc.
    try:
        res = supabase.table("prediction_log").select("*").execute()
        df = pd.DataFrame(res.data)
        winrate = (
            df['outcome'].value_counts(normalize=True).get('win', 0)
            if 'outcome' in df.columns else 0
        )
        total = len(df)
        avg_conf = df['confidence'].mean() if 'confidence' in df.columns else 0
        log_event("metrics", {"winrate": winrate, "total": total, "avg_conf": avg_conf})
        return {"winrate": winrate, "total": total, "avg_conf": avg_conf}
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"error": str(e)}

@app.get("/admin/logs")
def fetch_logs():
    try:
        res = supabase.table("event_log").select("*").order("timestamp", desc=True).limit(100).execute()
        logs = res.data if res.data else []
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Fetch logs error: {e}")
        return {"error": str(e)}
