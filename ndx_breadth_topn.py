
import os, sys, time, io, json, re
import pandas as pd, numpy as np
import yfinance as yf
import requests as rq
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.utils import ensure_dir

OUT = "data/raw/ndx_breadth_topn.csv"
WIKI_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"

def get_constituents(limit: int = 20):
    try:
        r = rq.get(WIKI_URL, timeout=30)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        tickers = []
        for df in tables:
            cols = [str(c).lower() for c in df.columns]
            if any("ticker" in c for c in cols) or any("symbol" in c for c in cols):
                col = None
                for c in df.columns:
                    if "ticker" in str(c).lower() or "symbol" in str(c).lower():
                        col = c; break
                if col is None: continue
                vals = list(pd.Series(df[col]).dropna().astype(str))
                vals = [re.sub(r"[^A-Za-z0-9\.-]", "", v).upper().replace(".", "-") for v in vals if v.strip()]
                tickers = list(dict.fromkeys(vals))
                break
        if not tickers:
            tickers = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","AVGO","COST","PEP","ADBE"]
        return tickers[:limit]
    except Exception:
        return ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","AVGO","COST","PEP","ADBE"][:limit]

def compute_breadth(tickers, lookback: int = 50):
    hist = {}
    for t in tickers:
        try:
            df = yf.download(t, period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
            if df is not None and not df.empty:
                hist[t] = df["Close"].rename(t)
        except Exception:
            continue
    if not hist:
        return pd.DataFrame(columns=["pct_above_50dma"])
    prices = pd.DataFrame(hist).sort_index()
    sma = prices.rolling(lookback).mean()
    breadth = (prices >= sma).sum(axis=1) / prices.shape[1] * 100.0
    return breadth.to_frame("pct_above_50dma")

def main():
    tickers = get_constituents(limit=20)
    breadth = compute_breadth(tickers)
    ensure_dir(OUT)
    if breadth.empty:
        # keep old file if exists
        if os.path.exists(OUT):
            print("Breadth empty; keep previous file.")
        else:
            pd.DataFrame({"pct_above_50dma":[]}).to_csv(OUT, index=True)
            print("Breadth empty; wrote placeholder.")
    else:
        breadth.to_csv(OUT, index=True)
        print(f"saved {OUT}, rows={len(breadth)}")

if __name__ == "__main__":
    main()
