
import os, sys, io, time
import pandas as pd, numpy as np, requests as rq
from datetime import datetime as dt
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.utils import ensure_dir, ts_now_iso

OUT = "data/raw/naaim_exposure.csv"

CANDIDATES = [
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index_data.csv",
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
]

def fetch() -> pd.DataFrame:
    for url in CANDIDATES:
        try:
            r = rq.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 64:
                df = pd.read_csv(io.BytesIO(r.content))
                # Normalize columns
                cols = [c.lower().strip() for c in df.columns]
                df.columns = cols
                # try common shapes
                if "date" in df.columns:
                    vcol = next((c for c in df.columns if c not in ("date",)), df.columns[-1])
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    df = df[["date", vcol]].dropna()
                    df = df.rename(columns={vcol: "value"}).set_index("date").sort_index()
                else:
                    # hope first col is date
                    dcol = df.columns[0]
                    vcol = df.columns[-1]
                    df[dcol] = pd.to_datetime(df[dcol], errors="coerce")
                    df = df[[dcol, vcol]].dropna()
                    df = df.rename(columns={dcol: "date", vcol: "value"}).set_index("date").sort_index()
                return df
        except Exception:
            continue
    # fallback: keep previous if exists
    if os.path.exists(OUT):
        try:
            df = pd.read_csv(OUT, parse_dates=[0], index_col=0)
            df.columns = ["value"]
            return df
        except Exception:
            pass
    # final: empty frame
    return pd.DataFrame(columns=["value"])

def main():
    df = fetch()
    ensure_dir(OUT)
    if df.empty:
        # write placeholder header to keep pipeline running
        pd.DataFrame({"value":[]}).to_csv(OUT)
        print("naaim empty; wrote placeholder.")
    else:
        df.to_csv(OUT)
        print(f"saved {OUT}, rows={len(df)}")

if __name__ == "__main__":
    main()
