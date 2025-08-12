
import os, json, time
import pandas as pd
import requests
import yfinance as yf

try:
    from core.utils import ensure_dir, write_json, ts_now_iso
except Exception:
    from tools.utils import ensure_dir, write_json, ts_now_iso

OUT = "docs/prices.json"
DEFAULT_TICKERS = os.getenv("PRICES_TICKERS", "SPY,QQQ,TQQQ").replace(" ", "").split(",")
AV_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "").strip()

def fetch_alpha_vantage(symbol: str, api_key: str):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "compact"
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "Note" in data or "Information" in data or "Error Message" in data:
        raise RuntimeError("AV premium or rate limited")
    ts = data.get("Time Series (Daily)") or {}
    rows = sorted(ts.items())
    out = []
    for d, row in rows:
        out.append([d, float(row.get("5. adjusted close") or row.get("4. close") or 0.0)])
    return out

def fetch_yf(symbol: str):
    df = yf.download(symbol, period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
    if df is None or df.empty:
        return []
    s = df["Close"]
    return [[pd.to_datetime(ix).strftime("%Y-%m-%d"), float(v)] for ix, v in s.dropna().items()]

def main():
    tickers = [t for t in DEFAULT_TICKERS if t]
    prices = {}
    meta = {"tickers": tickers, "source": ""}
    for t in tickers:
        series = []
        used = None
        if AV_KEY:
            try:
                series = fetch_alpha_vantage(t, AV_KEY); used="alphavantage"
            except Exception:
                series = []
        if not series:
            try:
                series = fetch_yf(t); used="yfinance"
            except Exception:
                series = []
        if series:
            prices[t] = series
    meta["source"] = used or "none"
    out = {"as_of": ts_now_iso(), "prices": prices, "meta": meta}
    write_json(OUT, out)
    print(f"wrote {OUT} tickers={list(prices)} source={meta['source']}")

if __name__ == "__main__":
    main()
