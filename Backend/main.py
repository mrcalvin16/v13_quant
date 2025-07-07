import os
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, Query
from supabase import create_client
from datetime import datetime, timedelta

app = FastAPI()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- DATA LOAD -------------------------

def load_tickers():
    try:
        nyse = pd.read_csv("nyse-listed.csv")['Symbol'].tolist()
        nasdaq = pd.read_csv("nasdaq-listed.csv")['Symbol'].tolist()
        return list(set(nyse + nasdaq))
    except Exception as e:
        print(f"Ticker load error: {e}")
        return []

TICKERS = load_tickers()

# -------------------- UTILS -----------------------------

def log_event(event, details):
    supabase.table("app_log").insert({
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "details": details
    }).execute()

def get_price(symbol):
    try:
        df = yf.Ticker(symbol).history(period="1d")
        if df.empty:
            return None
        return float(df['Close'].iloc[0])
    except Exception:
        return None

def get_history(symbol, period="1y"):
    try:
        df = yf.Ticker(symbol).history(period=period)
        return df.reset_index().to_dict('records')
    except Exception:
        return []

def get_earnings(symbol):
    try:
        tk = yf.Ticker(symbol)
        df = tk.earnings_dates
        return df.reset_index().to_dict('records') if not df.empty else []
    except Exception:
        return []

# ------------------- RECOMMENDATIONS ----------------------

def get_stock_recommendations(top_n=5):
    picks = []
    for symbol in TICKERS[:150]:  # Limit to 150 for perf. You can adjust.
        price = get_price(symbol)
        if not price or price < 1:  # skip penny
            continue
        # Simple momentum filter (customize for your model)
        try:
            df = yf.Ticker(symbol).history(period="5d")
            if len(df) < 5: continue
            perf = (df['Close'][-1] - df['Close'][0]) / df['Close'][0]
            if perf > 0.10:  # 10% up in 5d
                picks.append((symbol, perf, price))
        except Exception:
            continue
    picks = sorted(picks, key=lambda x: -x[1])[:top_n]
    log_event("get_stock_recommendations", {"tickers": [p[0] for p in picks]})
    return [{"symbol": s, "momentum": round(m, 3), "price": p} for s, m, p in picks]

# ------------------- OPTIONS RECOMMEND --------------------

def pick_best_options(symbol):
    try:
        tk = yf.Ticker(symbol)
        spot = get_price(symbol)
        expiry_list = tk.options
        best = []
        for expiry in expiry_list[:2]:
            chain = tk.option_chain(expiry)
            for side, df in [('call', chain.calls), ('put', chain.puts)]:
                df = df[df['openInterest'] > 20]
                for _, opt in df.iterrows():
                    if side == 'call' and opt['strike'] > spot:
                        est_return = (opt['strike'] - spot) / opt['lastPrice'] if opt['lastPrice'] > 0 else None
                    elif side == 'put' and opt['strike'] < spot:
                        est_return = (spot - opt['strike']) / opt['lastPrice'] if opt['lastPrice'] > 0 else None
                    else:
                        est_return = None
                    if est_return and est_return > 1:
                        best.append({
                            "type": side,
                            "expiry": expiry,
                            "strike": opt['strike'],
                            "lastPrice": opt['lastPrice'],
                            "bid": opt['bid'],
                            "ask": opt['ask'],
                            "openInterest": opt['openInterest'],
                            "impliedVolatility": opt['impliedVolatility'],
                            "est_return": round(est_return,2)
                        })
        picks = sorted(best, key=lambda x: -x['est_return'])[:5]
        log_event("pick_best_options", {"symbol": symbol, "options": picks})
        return picks
    except Exception as e:
        return [{"error": str(e)}]

# ------------------- PENNY STOCK / PUMP DETECTOR ---------

def detect_penny_stocks():
    picks = []
    for symbol in TICKERS[:300]:
        price = get_price(symbol)
        if price and price < 1:
            picks.append(symbol)
    log_event("detect_penny_stocks", {"results": picks})
    return picks

# ------------------- WATCHLIST ---------------------------

def add_watchlist(user_id, symbol):
    supabase.table("watchlist").insert({
        "user_id": user_id,
        "symbol": symbol,
        "added": datetime.utcnow().isoformat()
    }).execute()
    log_event("add_watchlist", {"user_id": user_id, "symbol": symbol})

def get_watchlist(user_id):
    res = supabase.table("watchlist").select("symbol").eq("user_id", user_id).execute()
    log_event("get_watchlist", {"user_id": user_id})
    return [r['symbol'] for r in res.data] if res.data else []

# ------------------- SEARCH -----------------------------

def search_tickers(query):
    found = [s for s in TICKERS if query.upper() in s]
    log_event("search_tickers", {"query": query, "results": found})
    return found

# ------------------- FASTAPI ROUTES ---------------------

@app.get("/recommendations/top")
def top_recommendations():
    recs = get_stock_recommendations()
    return {"buy_now": recs}

@app.get("/options/best")
def best_options(symbol: str = Query(..., description="Stock symbol (e.g. TSLA)")):
    picks = pick_best_options(symbol)
    return {"symbol": symbol, "best_options": picks}

@app.get("/tickers")
def all_tickers():
    return {"tickers": TICKERS}

@app.get("/historic")
def get_hist(symbol: str, period: str = "1y"):
    hist = get_history(symbol, period)
    return {"symbol": symbol, "history": hist}

@app.get("/earnings")
def earnings(symbol: str):
    data = get_earnings(symbol)
    return {"symbol": symbol, "earnings": data}

@app.get("/penny")
def penny_stocks():
    picks = detect_penny_stocks()
    return {"penny_stocks": picks}

@app.get("/watchlist")
def watchlist(user_id: str):
    wl = get_watchlist(user_id)
    return {"user_id": user_id, "watchlist": wl}

@app.post("/watchlist/add")
def add_to_watchlist(user_id: str, symbol: str):
    add_watchlist(user_id, symbol)
    return {"message": f"Added {symbol} to watchlist", "user_id": user_id}

@app.get("/search")
def search(query: str):
    found = search_tickers(query)
    return {"results": found}

# ------------------- METRICS/LOGGING/ADMIN ---------------

@app.get("/admin/logs")
def logs():
    data = supabase.table("app_log").select("*").order("timestamp", desc=True).limit(100).execute().data
    return {"logs": data}

@app.get("/admin/metrics")
def metrics():
    logs = supabase.table("app_log").select("*").execute().data
    return {"log_count": len(logs), "latest": logs[:5]}

# ---------------------------------------------------------

@app.get("/")
def root():
    return {"status": "OK", "features": [
        "buy now recommendations", "options picker", "historic data", "earnings", "penny detector",
        "watchlist", "search", "logging/metrics"
    ]}
