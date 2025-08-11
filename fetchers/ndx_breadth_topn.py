import time, pandas as pd, numpy as np
import yfinance as yf
from core.utils import ensure_dir

OUT = "data/raw/ndx_breadth_50dma.csv"
WIKI = "https://en.wikipedia.org/wiki/Nasdaq-100"


def constituents():
    try:
        tables = pd.read_html(WIKI)
        for t in tables:
            cols = [c.lower() for c in t.columns]
            if any("ticker" in c or "symbol" in c for c in cols):
                col = t.columns[["ticker" in c.lower() or "symbol" in c.lower() for c in cols].index(True)]
                tickers = t[col].astype(str).str.replace(r"\..*", "", regex=True).tolist()
                return tickers
    except Exception as e:
        print(f"wiki fetch failed: {e}")
    return []


def download_batch(batch):
    for attempt in range(3):
        try:
            df = yf.download(batch, period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
            return df
        except Exception as e:
            print(f"batch {batch} failed: {e}")
            time.sleep(1.2)
    return pd.DataFrame()


def compute():
    tickers = constituents()
    if not tickers:
        return pd.DataFrame(columns=["date", "pct_above"])
    closes = []
    for i in range(0, len(tickers), 25):
        batch = tickers[i : i + 25]
        df = download_batch(batch)
        if df is None or df.empty:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df = df["Close"]
        else:
            df = df[["Close"]]
            df.columns = [batch[0]]
        closes.append(df)
        time.sleep(1.2)
    if not closes:
        return pd.DataFrame(columns=["date", "pct_above"])
    px = pd.concat(closes, axis=1).sort_index()
    sma50 = px.rolling(50).mean()
    pct = (px >= sma50).sum(axis=1) / px.shape[1] * 100.0
    out = pct.to_frame("pct_above")
    out.index.name = "date"
    return out


def main():
    df = compute()
    ensure_dir(OUT)
    df.to_csv(OUT, index=True, date_format="%Y-%m-%d")
    print(f"saved {OUT}, rows={len(df)}")


if __name__ == "__main__":
    main()
