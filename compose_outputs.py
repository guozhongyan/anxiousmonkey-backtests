
import os, sys, json, pandas as pd, numpy as np, time, requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import ensure_dir, ts_now_iso

OUT_FACTORS = "docs/factors_namm50.json"

def read_csv_try(path, cols=None):
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").set_index("date")
        return df
    except Exception:
        return None

def to_series(df, cols):
    if df is None or df.empty:
        return None
    df = df.dropna()
    if df.empty:
        return None
    out = []
    for idx, row in df.iterrows():
        item = [idx.strftime("%Y-%m-%d")]
        for c in cols:
            v = row.get(c, np.nan)
            if pd.isna(v):
                v = None
            else:
                v = float(v)
            item.append(v)
        out.append(item)
    return out if out else None

def try_fetch_cnn_fgi():
    urls = [
        "https://production-files-cnnmoney-fear-and-greed-index.s3.amazonaws.com/production/fear-and-greed-index.json",
        "https://production-files-cnnmoney-fear-and-greed-index.s3.amazonaws.com/production/fng/streams/index.json",
        "https://production-files-cnnmoney-fear-and-greed-index.s3.amazonaws.com/production/fear-and-greed-index.json?noCache=1"
    ]
    for u in urls:
        try:
            r = requests.get(u, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code != 200: continue
            j = r.json()
            vals = []
            def dig(x):
                if isinstance(x, dict):
                    for v in x.values(): yield from dig(v)
                elif isinstance(x, list):
                    for v in x: yield from dig(v)
                else:
                    yield x
            for v in dig(j):
                try:
                    f = float(v)
                    if 0 <= f <= 100: vals.append(f)
                except Exception:
                    pass
            if vals:
                today = pd.Timestamp.utcnow().strftime("%Y-%m-%d")
                return [[today, float(vals[-1])]]
        except Exception:
            continue
    return None

def main():
    naaim = read_csv_try("data/raw/naaim_exposure.csv")
    ndx = read_csv_try("data/raw/ndx_breadth_50dma.csv")
    china = None
    for p in ["data/raw/china_proxy.csv","data/raw/china50_proxy.csv","data/raw/fxi_proxy.csv"]:
        if os.path.exists(p):
            china = read_csv_try(p)
            if china is not None: break
    fred = read_csv_try("data/raw/fred_macro.csv")
    vix = read_csv_try("data/raw/vix_fred.csv")

    out = {
        "as_of": ts_now_iso(),
        "factors": {
            "naaim_exposure": {"series": to_series(naaim, [naaim.columns[0]]) if naaim is not None else None},
            "fred_macro": {"series": to_series(fred, [c for c in ["DGS10","DFF"] if fred is not None and c in fred.columns]) if fred is not None else None},
            "ndx_breadth": {"series": to_series(ndx, [ndx.columns[0]]) if ndx is not None else None},
            "china_proxy": {"series": to_series(china, [china.columns[0]]) if china is not None else None},
            "vix": {"series": to_series(vix, ["VIX"]) if vix is not None else None},
            "cnn_fgi": {"series": try_fetch_cnn_fgi()}
        }
    }
    ensure_dir(OUT_FACTORS)
    with open(OUT_FACTORS,"w") as f:
        json.dump(out, f)
    print("wrote", OUT_FACTORS)

if __name__ == "__main__":
    main()
