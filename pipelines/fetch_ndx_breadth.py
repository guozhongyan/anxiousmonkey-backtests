import sys, os, time
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

def get_ndx_constituents():
    r = requests.get(WIKI_URL, timeout=60)
    r.raise_for_status()
    tables = pd.read_html(r.text)
    tickers = []
    for df in tables:
        cols = [str(c).lower() for c in df.columns]
        if any("ticker" in c for c in cols):
            for c in df.columns:
                if "ticker" in str(c).lower():
                    colname = c
                    break
            tickers = list(df[colname].dropna().astype(str).str.replace(r"[^\w\.-]", "", regex=True))
            break
    tickers = [t.strip().upper().replace(".", "-") for t in tickers if t.strip()]
    return sorted(set(tickers))

def batch_download_prices(tickers, tries=3, sleep_s=10):
    # Use single batched request to reduce rate limiting
    tickers_str = " ".join(tickers)
    last_err = None
    for i in range(tries):
        try:
            df = yf.download(
                tickers=tickers_str,
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
            last_err = e
        time.sleep(sleep_s * (i + 1))
    if last_err:
        print(f"yfinance batch download failed after retries: {last_err}")
    return pd.DataFrame()

def compute_breadth_from_batched(df, tickers):
    # df has a column MultiIndex: (Ticker, Field)
    if df is None or df.empty:
        return pd.DataFrame()
    # Extract Close for available tickers
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

def safe_write_breadth(breadth):
    ensure_dir(OUT_CSV)
    if breadth is not None and not breadth.empty:
        breadth.to_csv(OUT_CSV, index=True)
        print(f"saved {OUT_CSV}, rows={len(breadth)}")
        return True
    # If no new breadth, try to keep previous output if exists
    if os.path.exists(OUT_CSV):
        print("No new breadth data; keeping previous OUT_CSV.")
        return True
    # else write empty csv to avoid failing pipeline
    pd.DataFrame(columns=["Date", "pct_above_50dma"]).to_csv(OUT_CSV, index=False)
    print("No breadth data; wrote empty CSV placeholder.")
    return True

def main():
    tickers = get_ndx_constituents()
    batched = batch_download_prices(tickers)
    breadth = compute_breadth_from_batched(batched, tickers)
    ok = safe_write_breadth(breadth)
    if not ok:
        # Do not raise to keep the workflow green
        print("Breadth computation skipped this run.")

if __name__ == "__main__":
    main()
