    import os, json, time
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
            # choose the first column containing 'ticker'
            for c in df.columns:
                if "ticker" in str(c).lower():
                    colname = c
                    break
            tickers = list(df[colname].dropna().astype(str).str.replace(r"[^\w\.\-]", "", regex=True))
            break
    tickers = [t.strip().upper().replace(".", "-") for t in tickers if t.strip()]
    return sorted(set(tickers))

def compute_breadth(tickers):
    hist = {}
    for t in tickers:
        try:
            df = yf.download(t, period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
            if df is None or df.empty: 
                continue
            hist[t] = df["Close"].rename(t)
        except Exception:
            continue
    if not hist:
        raise RuntimeError("No Yahoo data for NDX tickers")
    prices = pd.DataFrame(hist).sort_index()
    sma50 = prices.rolling(50).mean()
    breadth = (prices >= sma50).sum(axis=1) / prices.shape[1] * 100.0
    return breadth.to_frame("pct_above_50dma")

def main():
    tickers = get_ndx_constituents()
    breadth = compute_breadth(tickers)
    ensure_dir(OUT_CSV)
    breadth.to_csv(OUT_CSV, index=True)
    print(f"saved {OUT_CSV}, rows={len(breadth)}")

if __name__ == "__main__":
    main()

