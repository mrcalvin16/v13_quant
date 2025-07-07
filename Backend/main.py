from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from datetime import datetime
from supabase import create_client
import os
import yfinance as yf
import pandas as pd
import json
import re
import logging

# --- Config & Supabase ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)
darkweb = supabase.table("signals").select("*").eq("strategy_id", "c2adcf36-2192-4c72-9097-a77e9bca015a").eq("ticker", ticker).execute()


# Logging config
logging.basicConfig(level=logging.INFO)

# --- FastAPI ---
app = FastAPI()
clients = []

# --- Helpers ---
def is_valid_uuid(val):
    return isinstance(val, str) and re.match(r'^[a-f0-9\-]{36}$', val)

def load_tickers():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    nyse_path = os.path.join(base_dir, "../nyse-listed.csv")
    other_path = os.path.join(base_dir, "../other-listed.csv")
    nyse = pd.read_csv(nyse_path)
    other = pd.read_csv(other_path)
    def get_symbols(df):
        for col in [
            "ACT Symbol", "CQS Symbol", "NASDAQ Symbol",
            "Symbol", "symbol", "Ticker", "ticker"
        ]:
            if col in df.columns:
                return df[col].dropna().unique().tolist()
        raise ValueError("No ticker column found in CSV.")
    nyse_symbols = get_symbols(nyse)
    other_symbols = get_symbols(other)
    return sorted(set(nyse_symbols + other_symbols))

tickers = load_tickers()

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

# --- Endpoints ---

@app.get("/")
def root():
    return {"status": "Backend is running."}

@app.get("/tickers")
def get_tickers():
    return tickers

@app.get("/recommendation/{ticker}")
def get_recommendation(ticker: str):
    if not is_valid_uuid(DARKWEB_STRATEGY_UUID):
        logging.error(f"Invalid strategy_id format: {DARKWEB_STRATEGY_UUID}")
        raise HTTPException(status_code=400, detail="Invalid strategy_id format")

    try:
        darkweb = supabase.table("signals").select("*").eq("strategy_id", DARKWEB_STRATEGY_UUID).eq("ticker", ticker).execute()
        pump_score = max([s["confidence"] for s in darkweb.data], default=0)
    except Exception as e:
        logging.error(f"Failed to query signals: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

    pred_score = 0.6  # Dummy score
    pred_price = 100  # Dummy price
    tk = yf.Ticker(ticker)
    cal = tk.calendar
    earnings_score = 0.5 if not cal.empty else 0
    expirations = tk.options
    if expirations:
        chain = tk.option_chain(expirations[0])
        calls = chain.calls
        opt_score = calls.impliedVolatility.mean() / 2
    else:
        opt_score = 0
    combined = (
        0.4 * pred_score +
        0.2 * pump_score +
        0.2 * earnings_score +
        0.2 * opt_score
    )
    return {
        "ticker": ticker,
        "pred_score": pred_score,
        "pump_score": pump_score,
        "earnings_score": earnings_score,
        "opt_score": opt_score,
        "combined_score": combined,
        "pred_price": pred_price
    }

@app.get("/recommendations/top")
def get_top_recommendations():
    try:
        res = supabase.table("recommendations").select("*").order("combined_score", desc=True).limit(10).execute()
        return res.data
    except Exception as e:
        logging.error(f"Failed to fetch recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-history")
def save_search(ticker: str):
    try:
        supabase.table("search_history").insert({
            "user_id": "anonymous",
            "ticker": ticker
        }).execute()
        return {"status": "saved"}
    except Exception as e:
        logging.error(f"Failed to save search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    if cal.empty:
        return {"next_earnings": None}
    next_earnings = cal.loc["Earnings Date"][0]
    return {"next_earnings": str(next_earnings)}

@app.get("/strategies")
def list_strategies():
    try:
        res = supabase.table("strategies").select("*").execute()
        return res.data
    except Exception as e:
        logging.error(f"Failed to fetch strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies")
def create_strategy(strategy: Strategy):
    try:
        res = supabase.table("strategies").insert(strategy.dict()).execute()
        return res.data[0]
    except Exception as e:
        logging.error(f"Failed to create strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subscribe")
def subscribe(sub: Subscription):
    if not is_valid_uuid(sub.strategy_id):
        logging.error(f"Invalid strategy_id format: {sub.strategy_id}")
        raise HTTPException(status_code=400, detail="Invalid strategy_id format")
    try:
        supabase.table("subscriptions").insert({
            "user_id": "anonymous",
            "strategy_id": sub.strategy_id
        }).execute()
        return {"status": "subscribed"}
    except Exception as e:
        logging.error(f"Failed to subscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subscriptions")
def get_subscriptions():
    try:
        res = supabase.table("subscriptions").select("*").eq("user_id", "anonymous").execute()
        return res.data
    except Exception as e:
        logging.error(f"Failed to fetch subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signals")
async def publish_signal(signal: Signal):
    if not is_valid_uuid(signal.strategy_id):
        logging.error(f"Invalid strategy_id format: {signal.strategy_id}")
        raise HTTPException(status_code=400, detail="Invalid strategy_id format")
    data = signal.dict()
    data["timestamp"] = datetime.utcnow().isoformat()
    try:
        supabase.table("signals").insert(data).execute()
        msg = json.dumps(data)
        for client in clients:
            await client.send_text(msg)
        return {"status": "signal published"}
    except Exception as e:
        logging.error(f"Failed to publish signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals")
def get_signals():
    try:
        res = supabase.table("signals").select("*").order("timestamp", desc=True).execute()
        return res.data
    except Exception as e:
        logging.error(f"Failed to fetch signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)
