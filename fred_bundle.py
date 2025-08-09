
import os, sys, requests as rq, pandas as pd
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.utils import ensure_dir

OUT = "data/raw/fred_namm50.csv"
SERIES = ["DGS10", "DFF"]  # 10Y yield, Fed funds

def fetch_series(series_id: str, api_key: str) -> pd.Series:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": api_key, "file_type": "json", "frequency": "d"}
    r = rq.get(url, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    obs = js.get("observations", [])
    df = pd.DataFrame(obs)
    if df.empty: 
        return pd.Series(dtype=float)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.set_index("date").sort_index()
    return df["value"].rename(series_id)

def main():
    api_key = os.environ.get("FRED_API_KEY", "")
    frames = []
    for sid in SERIES:
        try:
            s = fetch_series(sid, api_key)
            if not s.empty: frames.append(s)
        except Exception:
            continue
    if not frames:
        # keep previous if exists
        if os.path.exists(OUT):
            print("fred empty; keep previous file.")
            return
        else:
            pd.DataFrame(columns=SERIES).to_csv(OUT)
            print("fred empty; wrote placeholder.")
            return
    df = pd.concat(frames, axis=1).sort_index()
    ensure_dir(OUT)
    df.to_csv(OUT)
    print(f"saved {OUT}, cols={list(df.columns)}")

if __name__ == "__main__":
    main()
