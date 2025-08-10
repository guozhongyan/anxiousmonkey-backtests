import os, sys, json, pandas as pd, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import ts_now_iso, to_json_ready, json_dump

NAAM_CSV = "data/raw/naaim_exposure.csv"
NDX_CSV  = "data/raw/ndx_breadth.csv"
CHINA_CSV= "data/raw/china_proxy_fxi.csv"
FRED_CSV = "data/raw/fred_namm50.csv"
OUT_JSON = "docs/factors_namm50.json"

def read_series_or_none(path, cols):
    try:
        df = pd.read_csv(path)
        if df is None or df.empty:
            return None
        df["date"] = pd.to_datetime(df[cols[0]])
        out = df.set_index("date")[[cols[1]]]
        out.columns = ["value"]
        out = out.dropna()
        if out.empty:
            return None
        return [[d.strftime("%Y-%m-%d"), float(v), 0.0] for d, v in out["value"].items()]
    except Exception as e:
        print(f"[warn] read {path} failed:", e)
        return None

def main():
    factors = {}

    # NAAIM
    s = read_series_or_none(NAAM_CSV, ["date","value"])
    factors["naaim_exposure"] = {"series": s} if s else {"series": None}

    # NDX breadth
    s = read_series_or_none(NDX_CSV, ["date","value"])
    factors["ndx_breadth"] = {"series": s} if s else {"series": None}

    # China proxy
    s = read_series_or_none(CHINA_CSV, ["date","value"])
    factors["china_proxy"] = {"series": s} if s else {"series": None}

    # FRED macro: 这里简单计算 DGS10 与 DFF 的利差
    fred = None
    try:
        df = pd.read_csv(FRED_CSV)
        if not df.empty and "DGS10" in df.columns and "DFF" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.dropna()
            df["spread"] = df["DGS10"] - df["DFF"]
            out = df.set_index("date")[["spread"]]
            fred = [[d.strftime("%Y-%m-%d"), float(v), 0.0] for d, v in out["spread"].items()]
    except Exception as e:
        print("[warn] fred compose failed:", e)
    factors["fred_macro"] = {"series": fred} if fred else {"series": None}

    payload = {"as_of": ts_now_iso(), "factors": factors}
    json_dump(payload, OUT_JSON)
    print(f"wrote {OUT_JSON} with keys: {list(factors.keys())}")

if __name__ == "__main__":
    main()
