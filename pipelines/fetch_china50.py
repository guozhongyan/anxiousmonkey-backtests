import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pandas as pd
import yfinance as yf
from tools.utils import ensure_dir

OUT_CSV = "data/raw/china50.csv"
TICKERS = ["FXI"]  # keep it simple & stable

def main():
    frames = []
    for t in TICKERS:
        try:
            df = yf.download(t, period="10y", interval="1d", auto_adjust=False, progress=False, threads=False)
            if df is None or df.empty:
                continue
            s = df["Adj Close"].rename(t)
            frames.append(s)
        except Exception:
            continue
    ensure_dir(OUT_CSV)
    if frames:
        out = pd.concat(frames, axis=1).sort_index()
        out.to_csv(OUT_CSV, index=True)
        print(f"saved {OUT_CSV}, cols={list(out.columns)}")
    else:
        pd.DataFrame(columns=["Date"] + TICKERS).to_csv(OUT_CSV, index=False)
        print("china50 empty; wrote placeholder.")

if __name__ == "__main__":
    main()
