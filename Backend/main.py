import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from datetime import datetime, timedelta
import yfinance as yf

# Supabase config
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

def load_tickers():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir) if 'Backend' in script_dir else script_dir

    files = [
        os.path.join(repo_root, "nyse-listed.csv"),
        os.path.join(repo_root, "other-listed.csv"),
    ]
    symbols = []
    for fname in files:
        if os.path.exists(fname):
            df = pd.read_csv(fname)
            symbol_cols = [col for col in df.columns if "symbol" in col.lower()]
            for col in symbol_cols:
                symbols += df[col].dropna().astype(str).unique().tolist()
        else:
            print(f"Warning: {fname} not found!")
    if not symbols:
        symbols = ["AAPL", "GOOG", "MSFT"]
    return sorted(set(symbols))

TICKERS = load_tickers()

# --- Simple Model/Signals ---
def get_stock_recommendations():
    # Placeholder logic: Real model would go here
    recs = []
    for symbol in TICKERS[:25]:
        price = float(yf.Ticker(symbol).history(period="1d")['Close'][-1:])
        if price < 15:
            tag = "penny"
        elif price > 300:
            tag = "bluechip"
        else:
            tag = "growth"
        recs.append({
            "symbol": symbol,
            "confidence": round(0.7 + 0.25*(price % 1), 2),
            "predicted_price": price * 1.03,
            "action": "buy",
            "tag": tag,
        })
    return sorted(recs, key=lambda r: r["confidence"], reverse=True)[:8]

def get_earnings_calendar(symbol):
    try:
        tk = yf.Ticker(symbol)
        cal = tk.earnings_dates
        if isinstance(cal, pd.DataFrame) and not cal.empty:
            return cal.head(5).to_dict(orient="records")
        else:
            return []
    except Exception:
        return []

def get_options_chain(symbol):
    try:
        tk = yf.Ticker(symbol)
        options_dates = tk.options
        if not options_dates:
            return []
        opt = tk.option_chain(options_dates[0])
        df = opt.calls if hasattr(opt, 'calls') else pd.DataFrame()
        if not df.empty:
            return df.head(10).to_dict(orient="records")
        return []
    except Exception:
        return []

def detect_pump_and_dumps():
    # Toy logic: penny stocks that jumped >20% yesterday
    results = []
    for symbol in TICKERS[:100]:
        try:
            data = yf.Ticker(symbol).history(period="2d")
            if len(data) < 2: continue
            pct = ((data['Close'][-1] - data['Close'][-2]) / data['Close'][-2]) * 100
            if pct > 20 and data['Close'][-1] < 5:
                results.append({
                    "symbol": symbol,
                    "pct_move": round(pct, 2),
                    "price": float(data['Close'][-1])
                })
        except Exception:
            continue
    return results

# --- Logging, Metrics, Learning ---
def log_prediction(symbol, action, predicted_price, timestamp=None):
    timestamp = timestamp or datetime.utcnow().isoformat()
    supabase.table("prediction_log").insert({
        "ticker": symbol,
        "action": action,
        "predicted_price": predicted_price,
        "timestamp": timestamp,
        "actual_price": None,
        "outcome": None,
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

def get_metrics():
    logs = supabase.table("prediction_log").select("*").execute().data
    total = len(logs)
    wins = len([l for l in logs if l.get("outcome") == "win"])
    losses = len([l for l in logs if l.get("outcome") == "loss"])
    win_rate = (wins / total) * 100 if total else 0
    return {
        "total_predictions": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
    }

# --- API Endpoints ---

@app.get("/tickers")
def list_tickers():
    return {"tickers": TICKERS}

@app.get("/recommendations/top")
def top_recommendations():
    recs = get_stock_recommendations()
    for rec in recs:
        log_prediction(rec["symbol"], rec["action"], rec["predicted_price"])
    return recs

@app.get("/earnings/{symbol}")
def earnings_view(symbol: str):
    return get_earnings_calendar(symbol)

@app.get("/options/{symbol}")
def options_view(symbol: str):
    return get_options_chain(symbol)

@app.get("/pumpdumps")
def pumpdumps():
    return detect_pump_and_dumps()

@app.get("/admin/metrics")
def metrics():
    update_prediction_outcomes()
    return get_metrics()

@app.get("/watchlist")
def get_watchlist():
    data = supabase.table("watchlist").select("*").execute().data
    return data

@app.post("/watchlist/add")
async def add_watchlist(req: Request):
    body = await req.json()
    ticker = body.get("ticker")
    supabase.table("watchlist").insert({"ticker": ticker}).execute()
    return {"success": True}

@app.get("/historic/{symbol}")
def get_historic(symbol: str):
    try:
        df = yf.Ticker(symbol).history(period="1y")
        return df.reset_index().to_dict(orient="records")
    except Exception:
        return []

# --- Optionally, a simple root check ---
@app.get("/")
def root():
    return {"status": "ok", "version": "1.1.0"}
