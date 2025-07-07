from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from supabase import create_client
import os
import yfinance as yf
import pandas as pd
import json
import threading
import time
import numpy as np

# --- Setup Supabase ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

app = FastAPI()
clients = []

# --- Models ---
class Strategy(BaseModel):
    name: str
    description: str
    tags: list

class Signal(BaseModel):
    strategy_id: str
    ticker: str
    action: str
    price_target: float
    confidence: float

class Subscription(BaseModel):
    strategy_id: str

class FlagRequest(BaseModel):
    prediction_id: int

# --- Ticker Loader ---
def load_tickers():
    nyse = pd.read_csv("nyse-listed.csv")
    other = pd.read_csv("other-listed.csv")
    nyse_symbols = nyse["ACT Symbol"].dropna().unique().tolist() if "ACT Symbol" in nyse else []
    other_symbols = other["NASDAQ Symbol"].dropna().unique().tolist() if "NASDAQ Symbol" in other else []
    return sorted(set(nyse_symbols + other_symbols))

tickers = load_tickers()

# --- Advanced Logging ---
def log_event(event_type, details):
    supabase.table("app_logs").insert({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": json.dumps(details)
    }).execute()

# --- Self-learning and Optimization ---
def get_latest_weights():
    res = supabase.table("prediction_weights").select("*").order("created_at", desc=True).limit(1).execute()
    if res.data:
        w = res.data[0]
        return [w['pred_score'], w['pump_score'], w['earnings_score'], w['opt_score']]
    else:
        return [0.4, 0.2, 0.2, 0.2]

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
            log_event("prediction_result", {"id": entry["id"], "ticker": ticker, "outcome": win, "actual_price": actual_price})
        except Exception as e:
            log_event("prediction_backfill_error", {"ticker": ticker, "error": str(e)})

def auto_optimize_weights():
    logs = supabase.table("prediction_log").select("*").neq("outcome", None).neq("flagged", True).execute().data
    if len(logs) < 30:
        return
    df = pd.DataFrame(logs)
    df["y"] = (df["outcome"] == "win").astype(int)
    X = df[["pred_score", "pump_score", "earnings_score", "opt_score"]]
    y = df["y"]
    from sklearn.linear_model import LinearRegression
    model = LinearRegression().fit(X, y)
    weights = model.coef_ / model.coef_.sum()
    supabase.table("prediction_weights").insert({
        "pred_score": float(weights[0]),
        "pump_score": float(weights[1]),
        "earnings_score": float(weights[2]),
        "opt_score": float(weights[3]),
    }).execute()
    log_event("weights_updated", {"weights": weights.tolist()})

def start_background_learning():
    def loop():
        while True:
            update_prediction_outcomes()
            auto_optimize_weights()
            time.sleep(12*3600)
    t = threading.Thread(target=loop, daemon=True)
    t.start()

@app.on_event("startup")
def startup_event():
    start_background_learning()

# --- Pump & Dump / Penny Stock Detector ---
def detect_pump_and_dump(ticker):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="30d", interval="1d")
        if hist.empty:
            return False, 0
        # Penny stock if price < $5
        last_close = hist["Close"][-1]
        is_penny = last_close < 5
        # Pump detection: spike in volume & price
        price_change = (hist["Close"][-1] - hist["Close"][-5]) / hist["Close"][-5]
        volume_spike = hist["Volume"][-5:].mean() > 2 * hist["Volume"][:-5].mean()
        pump_score = 0.7*price_change + 0.3*(volume_spike)
        flagged = is_penny or (pump_score > 0.2)
        return flagged, pump_score
    except Exception as e:
        log_event("pump_detection_error", {"ticker": ticker, "error": str(e)})
        return False, 0

# --- API Endpoints ---
@app.get("/")
def root():
    return {"status": "Backend is running."}

@app.get("/tickers")
def get_tickers():
    return tickers

@app.get("/recommendation/{ticker}")
def get_recommendation(ticker: str):
    pred_score = 0.6
    pred_price = 100
    # Replace UUID below with your real one!
    darkweb = supabase.table("signals").select("*").eq("strategy_id", "fd4f6249-0769-4d89-8322-3789fccf7a5a").eq("ticker", ticker).execute()
    pump_score = max([s["confidence"] for s in darkweb.data], default=0)
    flagged, pnd_score = detect_pump_and_dump(ticker)
    if pnd_score > pump_score:
        pump_score = pnd_score
    tk = yf.Ticker(ticker)
    cal = tk.calendar
    earnings_score = 0.5 if isinstance(cal, pd.DataFrame) and not cal.empty else 0
    expirations = tk.options
    if expirations:
        chain = tk.option_chain(expirations[0])
        calls = chain.calls
        opt_score = calls.impliedVolatility.mean() / 2 if not calls.empty else 0
    else:
        opt_score = 0
    weights = get_latest_weights()
    combined = (
        weights[0] * pred_score +
        weights[1] * pump_score +
        weights[2] * earnings_score +
        weights[3] * opt_score
    )
    log = {
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
        "pred_score": pred_score,
        "pump_score": pump_score,
        "pnd_flagged": flagged,
        "pnd_score": pnd_score,
        "earnings_score": earnings_score,
        "opt_score": opt_score,
        "combined_score": combined,
        "predicted_price": pred_price
    }
    supabase.table("prediction_log").insert(log).execute()
    log_event("recommendation", log)
    return log

@app.get("/pumpdumps")
def pump_and_dump_screen():
    flagged = []
    for t in tickers:
        flag, score = detect_pump_and_dump(t)
        if flag:
            flagged.append({"ticker": t, "pump_score": score})
    flagged = sorted(flagged, key=lambda x: -x["pump_score"])[:20]
    log_event("pumpdumps_listed", {"count": len(flagged)})
    return flagged

@app.get("/recommendations/top")
def get_top_recommendations():
    res = supabase.table("prediction_log").select("*").order("combined_score", desc=True).limit(10).execute()
    return res.data

@app.post("/search-history")
def save_search(ticker: str):
    supabase.table("search_history").insert({
        "user_id": "anonymous",
        "ticker": ticker
    }).execute()
    log_event("search", {"ticker": ticker})
    return {"status": "saved"}

@app.get("/options/{ticker}")
def get_options(ticker: str):
    tk = yf.Ticker(ticker)
    exps = tk.options
    all_chains = []
    for exp in exps[:2]:
        chain = tk.option_chain(exp)
        calls = chain.calls
        puts = chain.puts
        calls["type"] = "call"
        puts["type"] = "put"
        calls["expiration"] = exp
        puts["expiration"] = exp
        all_chains.extend([calls, puts])
    df = pd.concat(all_chains).reset_index(drop=True)
    return df.to_dict(orient="records")

@app.get("/earnings/{ticker}")
def get_earnings(ticker: str):
    tk = yf.Ticker(ticker)
    cal = tk.calendar
    if isinstance(cal, pd.DataFrame) and not cal.empty:
        next_earnings = cal.loc["Earnings Date"][0]
        return {"next_earnings": str(next_earnings)}
    return {"next_earnings": None}

@app.get("/strategies")
def list_strategies():
    res = supabase.table("strategies").select("*").execute()
    return res.data

@app.post("/strategies")
def create_strategy(strategy: Strategy):
    res = supabase.table("strategies").insert(strategy.dict()).execute()
    return res.data[0]

@app.post("/subscribe")
def subscribe(sub: Subscription):
    supabase.table("subscriptions").insert({
        "user_id": "anonymous",
        "strategy_id": sub.strategy_id
    }).execute()
    return {"status": "subscribed"}

@app.get("/subscriptions")
def get_subscriptions():
    res = supabase.table("subscriptions").select("*").eq("user_id", "anonymous").execute()
    return res.data

@app.post("/signals")
async def publish_signal(signal: Signal):
    data = signal.dict()
    data["timestamp"] = datetime.utcnow().isoformat()
    supabase.table("signals").insert(data).execute()
    msg = json.dumps(data)
    for client in clients:
        await client.send_text(msg)
    log_event("signal_published", data)
    return {"status": "signal published"}

@app.get("/signals")
def get_signals():
    res = supabase.table("signals").select("*").order("timestamp", desc=True).execute()
    return res.data

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

@app.post("/admin/flag")
def flag_bad_prediction(flag: FlagRequest):
    supabase.table("prediction_log").update({"flagged": True}).eq("id", flag.prediction_id).execute()
    log_event("flagged", {"prediction_id": flag.prediction_id})
    return {"status": "flagged"}

@app.get("/admin/logs")
def get_app_logs():
    res = supabase.table("app_logs").select("*").order("timestamp", desc=True).limit(100).execute()
    return res.data

@app.get("/admin/metrics")
def admin_metrics():
    plogs = supabase.table("prediction_log").select("*").limit(1000).execute().data
    if not plogs:
        return {}
    df = pd.DataFrame(plogs)
    win_rate = df["outcome"].value_counts(normalize=True).get("win", 0)
    loss_rate = df["outcome"].value_counts(normalize=True).get("loss", 0)
    avg_conf = df["combined_score"].mean() if "combined_score" in df else 0
    flagged = df["flagged"].sum() if "flagged" in df else 0
    weights = get_latest_weights()
    return {
        "win_rate": win_rate,
        "loss_rate": loss_rate,
        "avg_confidence": avg_conf,
        "flagged_count": flagged,
        "weights": weights
    }

# Add more as needed...
