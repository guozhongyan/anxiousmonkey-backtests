import sys, os, time, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from tools.utils import ensure_dir

OUT_CSV = "data/raw/ndx_breadth_50dma.csv"
WIKI_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"

TOP_N = int(os.environ.get("NDX_TOP_N", "10"))

def get_ndx_constituents_topN(n=10):
    r = requests.get(WIKI_URL, timeout=60)
    r.raise_for_status()
    tables = pd.read_html(r.text)
    best = None
    for df in tables:
        cols = [str(c).lower() for c in df.columns]
        if any("weight" in c for c in cols) and any("ticker" in c for c in cols):
            best = df
            break
    if best is None:
        for df in tables:
            cols = [str(c).lower() for c in df.columns]
            if any("ticker" in c for c in cols):
                best = df
                break
    if best is None:
        raise RuntimeError("NDX table not found on Wikipedia")
    cols = {str(c).lower(): c for c in best.columns}
    tick_col = None
    for k,v in cols.items():
        if "ticker" in k:
            tick_col = v
            break
    tickers = list(best[tick_col].dropna().astype(str).str.replace(r"[^\w\.-]", "", regex=True))
    if any("weight" in k for k in cols.keys()):
        wcol = None
        for k,v in cols.items():
            if "weight" in k:
                wcol = v
                break
        weights = pd.to_numeric(best[wcol].astype(str).str.replace("%",""), errors="coerce")
        dfw = pd.DataFrame({"ticker": tickers, "w": weights}).dropna().sort_values("w", ascending=False)
        tickers = list(dfw["ticker"])
    tickers = [t.strip().upper().replace(".", "-") for t in tickers if t.strip()]
    tickers = sorted(dict.fromkeys(tickers), key=tickers.index)[:n]
    return tickers

def batch_download(tickers, tries=3, sleep_s=8):
    last = None
    for i in range(tries):
        try:
            df = yf.download(
                tickers=" ".join(tickers),
                period="2y",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=True,
                group_by="ticker",
            )
            if df is not None and not df.empty:
                return df
        except Exception as e:
            last = e
        time.sleep(sleep_s * (i + 1))
    if last:
        print(f"yfinance batch err: {last}")
    return pd.DataFrame()

def compute_breadth(df, tickers):
    if df is None or df.empty:
        return pd.DataFrame()
    closes = {}
    for t in tickers:
        try:
            s = df[(t, "Close")].dropna()
            if s.empty: 
                continue
            closes[t] = s.rename(t)
        except Exception:
            continue
    if not closes:
        return pd.DataFrame()
    prices = pd.DataFrame(closes).sort_index()
    sma50 = prices.rolling(50).mean()
    breadth = (prices >= sma50).sum(axis=1) / prices.shape[1] * 100.0
    return breadth.to_frame("pct_above_50dma")

def main():
    tickers = get_ndx_constituents_topN(TOP_N)
    df = batch_download(tickers)
    breadth = compute_breadth(df, tickers)
    ensure_dir(OUT_CSV)
    if breadth is not None and not breadth.empty:
        breadth.to_csv(OUT_CSV, index=True)
        print(f"saved {OUT_CSV}, rows={len(breadth)}")
    else:
        if os.path.exists(OUT_CSV):
            print("Breadth empty; keep previous file.")
        else:
            pd.DataFrame(columns=["Date","pct_above_50dma"]).to_csv(OUT_CSV, index=False)
            print("Breadth empty; wrote placeholder.")

if __name__ == "__main__":
    main()
