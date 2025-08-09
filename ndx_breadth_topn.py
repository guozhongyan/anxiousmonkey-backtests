
import os, time, requests, pandas as pd, numpy as np
from tools.utils import ensure_dir

ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY") or os.environ.get("ALPHAVANTAGE")
OUT = "data/raw/ndx_breadth_topn.csv"

DEFAULT_TICKERS = ["NVDA","MSFT","AAPL","AMZN","META","GOOGL","AVGO","COST","AMD","TSLA"]

def fetch_daily(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=compact&apikey={api_key}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    j = r.json()
    if "Error Message" in j or "Note" in j:
        raise RuntimeError(j.get("Error Message") or j.get("Note"))
    ts = j.get("Time Series (Daily)", {})
    rows = []
    for d, o in ts.items():
        try:
            rows.append((pd.Timestamp(d), float(o["5. adjusted close"])))
        except Exception:
            continue
    rows.sort()
    return pd.DataFrame(rows, columns=["date","close"]).set_index("date")

def sma(s, n):
    return s.rolling(n).mean()

def main():
    if not ALPHAVANTAGE_API_KEY:
        raise SystemExit("Set ALPHAVANTAGE_API_KEY in GitHub Secrets/Env.")
    topn = int(os.environ.get("NDX_TOPN","5"))
    tickers = DEFAULT_TICKERS[:topn]
    results = []
    for i, sym in enumerate(tickers):
        try:
            df = fetch_daily(sym, ALPHAVANTAGE_API_KEY)
            df["sma50"] = sma(df["close"], 50)
            df["ge50"] = (df["close"] >= df["sma50"]).astype(int)
            results.append(df[["ge50"]].rename(columns={"ge50": sym}))
            if i < len(tickers)-1:
                time.sleep(12)
        except Exception as e:
            ser = pd.Series([np.nan], index=[pd.Timestamp.utcnow().normalize()])
            results.append(ser.to_frame(sym))
    if not results:
        raise SystemExit("No breadth components fetched.")
    joined = pd.concat(results, axis=1).sort_index()
    joined["pct_above_50dma"] = (joined.fillna(0).sum(axis=1) / len(tickers))*100.0
    out = joined[["pct_above_50dma"]].dropna(how="all")
    ensure_dir(OUT)
    out.to_csv(OUT)
    print(f"saved {OUT}, rows={len(out)}")

if __name__ == "__main__":
    main()
