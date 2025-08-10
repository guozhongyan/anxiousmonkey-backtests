import os, sys, time, json, pandas as pd, requests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import ts_now_iso, ensure_dir, json_dump

OUT_JSON = "docs/prices.json"
AV_KEY = os.environ.get("ALPHAVANTAGE_API_KEY","").strip()
TICKERS = [t.strip().upper() for t in os.environ.get("PRICES_TICKERS","SPY,QQQ,TQQQ,SOXL").split(",") if t.strip()]

def fetch_av_daily(symbol: str):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=compact&apikey={AV_KEY}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()
    ts = js.get("Time Series (Daily)", {})
    if not ts:
        raise RuntimeError(f"AV empty for {symbol}: {js}")
    items = sorted(ts.items())[-2:]
    last_date, last = items[-1]
    prev_date, prev = items[-2]
    last_c = float(last["5. adjusted close"])
    prev_c = float(prev["5. adjusted close"])
    chg = (last_c/prev_c - 1.0) * 100.0
    return {"price": round(last_c, 4), "change_pct": round(chg, 3), "date": last_date}

def fetch_yf_last(symbol: str):
    import yfinance as yf
    df = yf.download(symbol, period="10d", interval="1d", auto_adjust=True, progress=False, threads=False)
    if df is None or df.empty or len(df) < 2: 
        raise RuntimeError("yf empty")
    last = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])
    chg = (last/prev - 1.0) * 100.0
    last_date = df.index[-1].strftime("%Y-%m-%d")
    return {"price": round(last,4), "change_pct": round(chg,3), "date": last_date}

def main():
    out = {"as_of": ts_now_iso(), "symbols": {}}
    for i, sym in enumerate(TICKERS):
        try:
            if AV_KEY:
                # AV 限速 5/min，简单节流
                if i and i % 4 == 0:
                    time.sleep(15)
                out["symbols"][sym] = fetch_av_daily(sym)
            else:
                out["symbols"][sym] = fetch_yf_last(sym)
        except Exception as e:
            print(f"[warn] price fetch failed for {sym}:", e)
            out["symbols"][sym] = None
    json_dump(out, OUT_JSON)
    print(f"wrote {OUT_JSON} for {len(TICKERS)} symbols")

if __name__ == "__main__":
    main()
