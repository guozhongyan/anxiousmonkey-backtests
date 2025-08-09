import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from tools.utils import ensure_dir, to_json_ready, zscore, ts_now_iso

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT_JSON = os.path.join(ROOT, 'docs', 'factors_namm50.json')

def _read_first_series(csv_path, prefer_cols=None):
    if prefer_cols is None: prefer_cols = []
    if not os.path.exists(csv_path): 
        return pd.Series(dtype=float)
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.Series(dtype=float)
    if df.empty or df.shape[1] <= 1:
        return pd.Series(dtype=float)
    # normalize date
    # find date-like column (first column) if it's name like 'Date' or unnamed
    date_col = df.columns[0]
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    except Exception:
        # try default index
        pass
    # choose first numeric column
    cols = list(df.columns)
    for c in prefer_cols:
        if c in cols:
            s = pd.to_numeric(df[c], errors='coerce').dropna()
            s.name = c
            return s
    # any numeric
    for c in cols:
        s = pd.to_numeric(df[c], errors='coerce')
        if s.notna().any():
            s = s.dropna()
            s.name = c
            return s
    return pd.Series(dtype=float)

def _read_frame(csv_path):
    if not os.path.exists(csv_path): 
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame()
    if df.empty: return pd.DataFrame()
    date_col = df.columns[0]
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    except Exception:
        pass
    # coerce numerics
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(how='all')
    return df

def build_payload():
    payload = {"as_of": ts_now_iso(), "factors": {}}

    # NAAIM Exposure
    naaim = _read_first_series(os.path.join(RAW, 'naaim_exposure.csv'), prefer_cols=['exposure','naaim','value'])
    if not naaim.empty:
        payload["factors"]["naaim_exposure"] = {
            "latest": float(naaim.dropna().iloc[-1]),
            "series": to_json_ready(naaim.to_frame(naaim.name), [naaim.name])
        }

    # NDX breadth (pct above 50dma)
    ndx = _read_first_series(os.path.join(RAW, 'ndx_breadth_50dma.csv'), prefer_cols=['pct_above_50dma'])
    if not ndx.empty:
        payload["factors"]["ndx_breadth_50dma"] = {
            "latest": float(ndx.dropna().iloc[-1]),
            "series": to_json_ready(ndx.to_frame(ndx.name), [ndx.name])
        }

    # China50 (FXI)
    chn = _read_first_series(os.path.join(RAW, 'china50.csv'), prefer_cols=['FXI'])
    if not chn.empty:
        payload["factors"]["china50_fxi"] = {
            "latest": float(chn.dropna().iloc[-1]),
            "series": to_json_ready(chn.to_frame(chn.name), [chn.name])
        }

    # FRED multi-series
    fred = _read_frame(os.path.join(RAW, 'fred_namm50.csv'))
    if not fred.empty:
        cols = list(fred.columns)
        payload["factors"]["fred_macro"] = {
            "columns": cols,
            "latest": {c: (None if pd.isna(fred[c].dropna().iloc[-1]) else float(fred[c].dropna().iloc[-1])) for c in cols if fred[c].notna().any()},
            "series": to_json_ready(fred, cols)
        }

    return payload

def main():
    data = build_payload()
    ensure_dir(OUT_JSON)
    with open(OUT_JSON, "w") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print(f"wrote {OUT_JSON}, keys={list(data['factors'].keys())}")

if __name__ == "__main__":
    main()
