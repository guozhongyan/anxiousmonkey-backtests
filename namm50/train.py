
import os
import time
import requests
import pandas as pd
import yfinance as yf

from core.utils import ts_now_iso, write_json

AV_URL = "https://www.alphavantage.co/query"

def _from_av_json(data: dict) -> pd.Series:
    # Accept both adjusted and non-adjusted
    key_daily = None
    for k in data.keys():
        if "Time Series (Daily)" in k:
            key_daily = k
            break
    if not key_daily:
        raise KeyError("No 'Time Series (Daily)' in payload")
    ts = data[key_daily]
    df = pd.DataFrame.from_dict(ts, orient="index")
    # prefer adjusted close if present
    cols_lc = {c.lower(): c for c in df.columns}
    price_col = None
    for cand in ["5. adjusted close", "4. close", "close", "adj close"]:
        if cand in cols_lc:
            price_col = cols_lc[cand]
            break
    if price_col is None:
        raise KeyError("No close/adjusted close in AV payload")
    # coerce numeric
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    s = df[price_col]
    s.index = pd.to_datetime(s.index)
    s = s.sort_index().rename("close").dropna()
    return s

def fetch_yf_daily(symbol: str) -> pd.Series:
    t = yf.Ticker(symbol)
    df = t.history(period="max", auto_adjust=True)
    if df is None or df.empty or "Close" not in df.columns:
        raise RuntimeError("yfinance daily fetch failed.")
    s = df["Close"].rename("close").dropna()
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    return s

def fetch_alpha_daily(symbol: str, api_key: str, outputsize: str = "full",
                      max_retries: int = 8, cooldown_sec: int = 15) -> pd.Series:
    """Try AlphaVantage first; on rate-limit/Note/Information fall back to yfinance."""
    if not api_key:
        return fetch_yf_daily(symbol)

    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": api_key,
    }
    last_err = None
    for i in range(max_retries):
        try:
            r = requests.get(AV_URL, params=params, timeout=30)
            data = r.json()
            if any("Time Series (Daily)" in k for k in data.keys()):
                return _from_av_json(data)
            if "Note" in data or "Information" in data:
                msg = data.get("Note") or data.get("Information")
                print(f"[namm50] AV backoff ({i+1}/{max_retries}): {msg}")
                time.sleep(cooldown_sec)
                continue
            last_err = RuntimeError(f"Unexpected keys: {list(data.keys())[:5]}")
        except Exception as e:
            last_err = e
        time.sleep(1)
    print(f"[namm50] AlphaVantage failed after retries: {last_err}. Falling back to yfinance.")
    return fetch_yf_daily(symbol)

def prep_features_prices(symbol: str) -> pd.DataFrame:
    api_key = os.getenv("ALPHAVANTAGE_API_KEY", "")
    outputsize = "compact" if os.getenv("LITE", "0") in ("1", "true", "True") else "full"
    prices = fetch_alpha_daily(symbol, api_key, outputsize=outputsize)
    df = pd.DataFrame({"close": prices})
    df["ret_1d"] = df["close"].pct_change()
    df["ma_20"] = df["close"].rolling(20).mean()
    df["ma_50"] = df["close"].rolling(50).mean()
    df["ma_200"] = df["close"].rolling(200).mean()
    df = df.dropna()
    return df

def main(symbol: str = None):
    symbol = symbol or os.getenv("SYMBOL", "SPY")
    print(f"[namm50] Training NAMM-50 on {symbol}")
    df = prep_features_prices(symbol)
    weights = {"NAAM": 1.0, "FRED": 0.0, "NDX50": 0.0, "CHINA": 0.0}
    out = {
        "as_of": ts_now_iso(),
        "model": "NAMM-50",
        "version": "v0.1-hotfix-av-fallback",
        "weights": weights,
        "latest": {"rows": int(len(df))}
    }
    os.makedirs("docs/models", exist_ok=True)
    write_json("docs/models/namm50.json", out, indent=2)
    print("wrote docs/models/namm50.json")

if __name__ == "__main__":
    main()
