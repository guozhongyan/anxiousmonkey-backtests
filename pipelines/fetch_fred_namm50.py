import sys, os, time, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import requests
from tools.utils import ensure_dir

OUT_CSV = "data/raw/fred_namm50.csv"

# Allow overriding series via env (comma-separated), fallback to common macro series
DEFAULT_SERIES = ["DGS10", "DFF"]
SERIES = [s.strip() for s in os.environ.get("NAMM50_SERIES", ",".join(DEFAULT_SERIES)).split(",") if s.strip()]

def fetch_fred_series(series_id, api_key, tries=3, sleep_s=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_start": "2010-01-01",
                },
                timeout=30,
            )
            r.raise_for_status()
            j = r.json()
            obs = j.get("observations", [])
            if not obs:
                return pd.Series(dtype=float, name=series_id)
            s = pd.Series(
                [float(x["value"]) if x["value"] not in (".", "") else None for x in obs],
                index=pd.to_datetime([x["date"] for x in obs]),
                name=series_id,
            ).dropna()
            return s
        except Exception as e:
            last = e
        time.sleep(sleep_s * (i + 1))
    if last:
        print(f"FRED fetch failed for {series_id}: {last}")
    return pd.Series(dtype=float, name=series_id)

def main():
    api_key = os.environ.get("FRED_API_KEY", "")
    ensure_dir(OUT_CSV)
    frames = []
    for sid in SERIES:
        s = fetch_fred_series(sid, api_key)
        if not s.empty:
            frames.append(s)
    if frames:
        out = pd.concat(frames, axis=1).sort_index()
        out.to_csv(OUT_CSV, index=True)
        print(f"saved {OUT_CSV}, cols={list(out.columns)}")
    else:
        # placeholder
        pd.DataFrame(columns=["Date"] + SERIES).to_csv(OUT_CSV, index=False)
        print("FRED empty; wrote placeholder.")

if __name__ == "__main__":
    main()
