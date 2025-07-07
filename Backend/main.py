from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
from supabase import create_client
import os
import yfinance as yf
import pandas as pd
import json

# Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

app = FastAPI()

# Load tickers
def load_tickers():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    nyse_path = os.path.join(base_dir, "../nyse-listed.csv")
    other_path = os.path.join(base_dir, "../other-listed.csv")
    nyse = pd.read_csv(nyse_path)
    other = pd.read_csv(other_path)

    def get_symbols(df):
        for col in [
            "ACT Symbol",
            "CQS Symbol",
            "NASDAQ Symbol",
            "Symbol",
            "symbol",
            "Ticker",
            "ticker",
        ]:
            if col in df.columns:
                return df[col].dropna().unique().tolist()
        raise ValueError("No ticker column found in CSV.")

    nyse_symbols = get_symbols(nyse)
    other_symbols = get_symbols(other)
    return sorted(set(nyse_symbols + other_symbols))

tickers = load_tickers()
clients = []

# Models
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

@app.get("/")
def root():
    return {"status": "Backend is running."}

@app.get("/tickers")
def get_tickers():
    return tickers

@app.get("/recommendation/{ticker}")
def get_recommendation(ticker: str):
    pred_score = 0.6  # Example dummy score
    pred_price = 100  # Example dummy price
    darkweb = supabase.table("signals").select("*").eq("strategy_id", "YOUR_DARKWEB_STRATEGY_UUID").eq("ticker", ticker).execute()
    pump_score = max([s["confidence"] for s in darkweb.data], default=0)
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
    res = supabase.table("recommendations").select("*").order("combined_score", desc=True).limit(10).execute()
    return res.data

@app.post("/search-history")
def save_search(ticker: str):
    supabase.table("search_history").insert({
        "user_id": "anonymous",
        "ticker": ticker
    }).execute()
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
    if cal.empty:
        return {"next_earnings": None}
    next_earnings = cal.loc["Earnings Date"][0]
    return {"next_earnings": str(next_earnings)}

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
