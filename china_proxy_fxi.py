import os, sys, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import safe_write_csv, write_placeholder_csv, load_prev_csv

OUT_CSV = "data/raw/china_proxy_fxi.csv"

def main():
    try:
        import yfinance as yf
        df = yf.download("FXI", period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
        if df is not None and not df.empty:
            out = df[["Close"]].rename(columns={"Close":"value"}).reset_index()
            out.columns = ["date","value"]
            safe_write_csv(out, OUT_CSV)
            print(f"saved {OUT_CSV}, rows={len(out)}")
            return
    except Exception as e:
        print("[warn] FXI fetch failed:", e)
    prev = load_prev_csv(OUT_CSV)
    if prev is not None and len(prev) > 0:
        safe_write_csv(prev, OUT_CSV)
        print(f"[fallback] kept previous {OUT_CSV}, rows={len(prev)}")
        return
    write_placeholder_csv(OUT_CSV, ["date","value"])
    print(f"[placeholder] wrote empty {OUT_CSV}")

if __name__ == "__main__":
    main()
