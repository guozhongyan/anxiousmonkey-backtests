
import os, sys, json, time, requests
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import ensure_dir

OUT_MACRO = "data/raw/fred_macro.csv"
OUT_VIX = "data/raw/vix_fred.csv"

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
BASE = "https://api.stlouisfed.org/fred/series/observations"

def fetch_series(series_id, start="2010-01-01"):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start,
    }
    r = requests.get(BASE, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    rows = []
    for ob in j.get("observations", []):
        d = ob.get("date")
        v = ob.get("value")
        try:
            x = float(v)
        except Exception:
            x = None
        rows.append([d, x])
    df = pd.DataFrame(rows, columns=["date","value"]).dropna()
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()

def main():
    if not FRED_API_KEY:
        print("FRED_API_KEY missing; skipping FRED fetch.")
        ensure_dir(OUT_MACRO); pd.DataFrame(columns=["DGS10","DFF"]).to_csv(OUT_MACRO)
        ensure_dir(OUT_VIX); pd.DataFrame(columns=["VIX"]).to_csv(OUT_VIX)
        return

    dgs10 = fetch_series("DGS10")
    dff = fetch_series("DFF")
    macro = pd.concat([dgs10.rename(columns={"value":"DGS10"}),
                       dff.rename(columns={"value":"DFF"})], axis=1).dropna()
    ensure_dir(OUT_MACRO)
    macro.to_csv(OUT_MACRO)
    print(f"saved {OUT_MACRO}, rows={len(macro)}")

    try:
        vix = fetch_series("VIXCLS").rename(columns={"value":"VIX"})
    except Exception as e:
        print("VIX fetch failed:", e); vix = pd.DataFrame(columns=["VIX"])
    ensure_dir(OUT_VIX); vix.to_csv(OUT_VIX)
    print(f"saved {OUT_VIX}, rows={len(vix)}")

if __name__ == "__main__":
    import pandas as pd
    main()
