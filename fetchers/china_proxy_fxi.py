
import os, sys
import pandas as pd
import yfinance as yf
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.utils import ensure_dir

OUT = "data/raw/china_proxy_fxi.csv"

def fetch():
    try:
        df = yf.download("FXI", period="5y", interval="1d", auto_adjust=True, progress=False, threads=False)
        if df is None or df.empty:
            return pd.DataFrame(columns=["close"])
        return df[["Close"]].rename(columns={"Close":"close"})
    except Exception:
        return pd.DataFrame(columns=["close"])

def main():
    df = fetch()
    ensure_dir(OUT)
    if df.empty:
        if os.path.exists(OUT):
            print("china50 empty; wrote placeholder.")
        else:
            pd.DataFrame({"close":[]}).to_csv(OUT, index=True)
            print("china50 empty; wrote placeholder.")
    else:
        df.to_csv(OUT)
        print(f"saved {OUT}, rows={len(df)}")

if __name__ == "__main__":
    main()
