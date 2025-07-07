from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from supabase import create_client
import os
import pandas as pd
import yfinance as yf
import json

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment vars (trim whitespace)
supabase_url = os.getenv("SUPABASE_URL", "").strip()
supabase_key = os.getenv("SUPABASE_KEY", "").strip()

if not supabase_url or not supabase_key:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set.")

supabase = create_client(supabase_url, supabase_key)

# Load tickers
def load_tickers():
    nyse = pd.read_csv("nyse-listed.csv")
    other = pd.read_csv("other-listed.csv")

    def get_symbols(df):
        for col in ["ACT Symbol", "Symbol", "symbol", "Ticker"]:
            if col in df.columns:
                return df[col].dropna().unique().tolist()
        raise ValueError("No ticker column found in CSV.")

    nyse_symbols = get_symbols(nyse)
    other_symbols = get_symbols(other)
    return sorted(set(nyse_symbols + other_symbols))

tickers = load_tickers()
clients = []

# Models
class Signal(BaseModel):
    strategy_id: str
    ticker: str
    action: str
    price_target: float
    confidence: float

# Root endpoint
@app.get("/")
def root():
    return {"status": "Backend is running."}

# Ticker list
@app.get("/tickers")
def get_tickers():
    return {"tickers": tickers}

# WebSocket endpoint
@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

# Publish new signal
@app.post("/signals")
async def publish_signal(signal: Signal):
    data = signal.dict()
    data["timestamp"] = datetime.utcnow().isoformat()
    supabase.table("signals").insert(data).execute()
    msg = json.dumps(data)
    for client in clients:
        await client.send_text(msg)
    return {"status": "Signal published."}

# List signals for ticker
@app.get("/signals/{symbol}")
def get_signals(symbol: str):
    res = supabase.table("signals").select("*").eq("ticker", symbol).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=str(res.error))
    return res.data

# Options chain
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

# Earnings calendar
@app.get("/earnings/{ticker}")
def get_earnings(ticker: str):
    tk = yf.Ticker(ticker)
    cal = tk.calendar
    if cal.empty:
        return {"next_earnings": None}
    next_earnings = cal.loc["Earnings Date"][0]
    return {"next_earnings": str(next_earnings)}

# Recommendation
@app.get("/recommendation/{ticker}")
def get_recommendation(ticker: str):
    pred_score = 0.6  # Example placeholder
    pred_price = 100  # Example placeholder
    darkweb = supabase.table("signals").select("*").eq("strategy_id", "YOUR_DARKWEB_STRATEGY_UUID").eq("ticker", ticker).execute()
    pump_score = max([s["confidence"] for s in darkweb.data], default=0)
    tk = yf.Ticker(ticker)
    cal = tk.calendar
    earnings_score = 0.5 if not cal.empty else 0
    expirations = tk.options
    chain = tk.option_chain(expirations[0])
    calls = chain.calls
    opt_score = calls.impliedVolatility.mean() / 2
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
