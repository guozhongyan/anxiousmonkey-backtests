
import os, requests, pandas as pd
from tools.utils import ensure_dir

FRED_API_KEY = os.environ.get("FRED_API_KEY")
OUT = "data/raw/fred_bundle.csv"

SERIES = {"DGS10":"10Y","DGS2":"2Y","UNRATE":"UNRATE","CPIAUCSL":"CPI"}

def fred_series(sid):
    params = {"series_id": sid, "api_key": FRED_API_KEY, "file_type": "json", "observation_start":"2000-01-01"}
    url = "https://api.stlouisfed.org/fred/series/observations"
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    rows = []
    for obs in j.get("observations", []):
        v = obs.get("value")
        if v is None or v == ".": continue
        rows.append((pd.Timestamp(obs["date"]), float(v)))
    return pd.DataFrame(rows, columns=["date","value"]).set_index("date")

def main():
    if not FRED_API_KEY:
        raise SystemExit("Set FRED_API_KEY in GitHub Secrets/Env.")
    frames = {}
    for sid, name in SERIES.items():
        try:
            df = fred_series(sid)
            frames[name] = df["value"]
        except Exception as e:
            print("FRED fail:", sid, e)
    if not frames:
        raise SystemExit("No FRED series fetched.")
    out = pd.DataFrame(frames).sort_index()
    ensure_dir(OUT)
    out.to_csv(OUT)
    print(f"saved {OUT}, rows={len(out)}")

if __name__ == "__main__":
    main()
