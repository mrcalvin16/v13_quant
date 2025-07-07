from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
from supabase import create_client
import os
import yfinance as yf
import pandas as pd
import json
import smtplib
from email.mime.text import MIMEText
import requests

# Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

app = FastAPI()

# Load tickers (no "data/" prefix)
def load_tickers():
    nyse = pd.read_csv("nyse-listed.csv")
    other = pd.read_csv("other-listed.csv")
    nyse_symbols = nyse["Symbol"].dropna().unique().tolist()
    other_symbols = other["Symbol"].dropna().unique().tolist()
    return sorted(set(nyse_symbols + other_symbols))

tickers = load_tickers()
clients = []

# Alerts
def send_email(recipient, subject, body):
    sender = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

def send_telegram(body):
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": body})

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

# WebSocket for signals
@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

@app.get("/tickers")
async def get_tickers():
    return tickers

@app.post("/strategies")
async def create_strategy(strategy: Strategy):
    res = supabase.table("strategies").insert(strategy.dict()).execute()
    return res.data[0]

@app.get("/strategies")
async def list_strategies():
    res = supabase.table("strategies").select("*").execute()
    return res.data

@app.post("/subscribe")
async def subscribe(sub: Subscription):
    supabase.table("subscriptions").insert({
        "user_id": "anonymous",
        "strategy_id": sub.strategy_id
    }).execute()
    return {"status": "subscribed"}

@app.get("/subscriptions")
async def get_subscriptions():
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
async def get_signals():
    res = supabase.table("signals").select("*").order("timestamp", desc=True).execute()
    return res.data

@app.get("/options/{ticker}")
async def get_options(ticker: str):
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
async def get_earnings(ticker: str):
    tk = yf.Ticker(ticker)
    cal = tk.calendar
    if cal.empty:
        return {"next_earnings": None}
    next_earnings = cal.loc["Earnings Date"][0]
    return {"next_earnings": str(next_earnings)}

@app.get("/recommendation/{ticker}")
async def get_recommendation(ticker: str):
    pred_score = 0.6  # Dummy example
    pred_price = 100  # Dummy example
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

@app.get("/recommendations/top")
async def get_top_recommendations():
    res = supabase.table("recommendations").select("*").order("combined_score", desc=True).limit(10).execute()
    return res.data

@app.post("/search-history")
async def save_search(ticker: str):
    supabase.table("search_history").insert({
        "user_id": "anonymous",
        "ticker": ticker
    }).execute()
    return {"status": "saved"}
