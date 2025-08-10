import os, sys, time, pandas as pd, numpy as np, requests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import safe_write_csv, write_placeholder_csv, load_prev_csv

OUT_CSV = "data/raw/ndx_breadth.csv"
WIKI_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"

def get_ndx_constituents():
    try:
        r = requests.get(WIKI_URL, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 AMBot"
        })
        r.raise_for_status()
        tables = pd.read_html(r.text)
        # 找包含 Ticker 列的表
        for df in tables:
            cols = [str(c).lower() for c in df.columns]
            if any("ticker" in c for c in cols):
                # 找到第一列含 ticker 的列名
                for c in df.columns:
                    if "ticker" in str(c).lower():
                        tickers = list(df[c].dropna().astype(str))
                        tickers = [t.strip().upper().replace(".","-") for t in tickers if t.strip()]
                        return sorted(set(tickers))
    except Exception as e:
        print("[warn] wiki ndx scrape failed:", e)
    # 兜底小集合
    return ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","TSLA","ADBE",
            "PEP","COST","NFLX","AMD","CSCO","TXN","INTC","QCOM","AMGN","HON"]

def breadth_topn(tickers, topn=25):
    import yfinance as yf
    tickers = list(tickers)[:max(5, topn)]
    tries = [topn, 15, 10, 8, 5]
    last_ok = None
    for n in tries:
        sub = tickers[:n]
        try:
            df = yf.download(sub, period="1y", interval="1d", auto_adjust=True, threads=False, progress=False, group_by="ticker")
            # 构造收盘价矩阵
            close = pd.DataFrame({t: df[t]["Close"] if (t in df and "Close" in df[t]) else pd.Series(dtype=float) for t in sub})
            close = close.dropna(how="all").sort_index()
            if close.empty:
                raise RuntimeError("empty close matrix")
            sma50 = close.rolling(50).mean()
            br = (close >= sma50).sum(axis=1) / close.shape[1] * 100.0
            s = br.rename("pct_above_50dma").reset_index()
            s.columns = ["date","value"]
            return s
        except Exception as e:
            print(f"[warn] yfinance breadth {n} failed:", e)
            last_ok = None
            time.sleep(2)
    return last_ok

def main():
    tickers = get_ndx_constituents()
    topn = int(os.environ.get("NDX_TOPN","25"))
    s = breadth_topn(tickers, topn=topn)
    if s is not None and len(s) > 0:
        safe_write_csv(s, OUT_CSV)
        print(f"saved {OUT_CSV}, rows={len(s)}")
        return
    prev = load_prev_csv(OUT_CSV)
    if prev is not None and len(prev) > 0:
        safe_write_csv(prev, OUT_CSV)
        print(f"[fallback] kept previous {OUT_CSV}, rows={len(prev)}")
        return
    write_placeholder_csv(OUT_CSV, ["date","value"])
    print(f"[placeholder] wrote empty {OUT_CSV}")

if __name__ == "__main__":
    main()
