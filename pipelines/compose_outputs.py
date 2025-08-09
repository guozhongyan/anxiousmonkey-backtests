
# -*- coding: utf-8 -*-
"""
compose_outputs.py
Builds docs/factors_namm50.json from raw CSVs.
Safe to run even when some inputs are missing or empty.
"""

import os, sys, json
from typing import Optional, List

# Make repo root importable (this file lives in /pipelines)
CUR_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CUR_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import pandas as pd

# utils
try:
    from tools.utils import ensure_dir, to_json_ready, ts_now_iso, zscore
except Exception:
    # Fallbacks to keep this script runnable even if utils shape changes
    def ensure_dir(path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    def ts_now_iso():
        return pd.Timestamp.utcnow().isoformat(timespec="seconds") + "Z"
    def to_json_ready(df: pd.DataFrame, cols=None):
        if cols is None:
            cols = list(df.columns)
        out = []
        for idx, row in df[cols].iterrows():
            ts = pd.Timestamp(idx).strftime("%Y-%m-%d") if isinstance(idx, (pd.Timestamp,)) else str(idx)
            item = [ts]
            for c in cols:
                v = row[c]
                if pd.isna(v):
                    v = None
                elif isinstance(v, (pd.Timestamp,)):
                    v = pd.Timestamp(v).strftime("%Y-%m-%d")
                else:
                    try:
                        v = float(v)
                    except Exception:
                        pass
                item.append(v)
            out.append(item)
        return out
    def zscore(s: pd.Series):
        s = s.astype(float)
        sd = s.std(ddof=0)
        if sd == 0 or pd.isna(sd):
            return pd.Series([0.0]*len(s), index=s.index)
        return (s - s.mean())/sd

DATA_DIR = os.path.join(ROOT_DIR, "data", "raw")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
OUT_JSON = os.path.join(DOCS_DIR, "factors_namm50.json")

# Helpers
def _read_csv(path: str, date_col: Optional[str]=None) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        # Guess date column
        if date_col and date_col in df.columns:
            idx = pd.to_datetime(df[date_col])
            df = df.drop(columns=[date_col])
        else:
            # Use first column as date if it looks like a date, else RangeIndex
            first = df.columns[0]
            try:
                idx = pd.to_datetime(df[first])
                df = df.drop(columns=[first])
            except Exception:
                idx = pd.RangeIndex(start=0, stop=len(df))
        df.index = idx
        df = df.sort_index()
        return df
    except Exception:
        return None

def _series_of(df: Optional[pd.DataFrame], col: str) -> Optional[pd.Series]:
    if df is None or df.empty:
        return None
    if col in df.columns:
        s = df[col]
    elif len(df.columns)==1:
        s = df.iloc[:,0]
    else:
        # take the last column as a best-effort
        s = df.iloc[:, -1]
    s = pd.to_numeric(s, errors="coerce")
    s = s.dropna()
    if s.empty:
        return None
    return s

def make_factor(name: str, s: Optional[pd.Series], weight: float) -> dict:
    if s is None or s.empty:
        return {"series": [], "weight": weight}
    df = pd.DataFrame({name: s})
    # Normalize index to date-like strings if possible
    try:
        df.index = pd.to_datetime(df.index)
    except Exception:
        pass
    series = to_json_ready(df, cols=[name])
    # Append per-point weight as the third element if consumer expects [ts, value, w]
    series = [ [row[0], row[1], weight] for row in series ]
    return {"series": series, "weight": weight}

def main():
    # Inputs
    naaim_csv = os.path.join(DATA_DIR, "naaim_exposure.csv")
    fred_csv  = os.path.join(DATA_DIR, "fred_namm50.csv")
    breadth_csv = os.path.join(DATA_DIR, "ndx_breadth_topn.csv")  # optional
    china_csv = os.path.join(DATA_DIR, "china_proxy_fxi.csv")     # optional

    naaim_df = _read_csv(naaim_csv)
    fred_df  = _read_csv(fred_csv)
    breadth_df = _read_csv(breadth_csv)
    china_df   = _read_csv(china_csv)

    # Build factors
    out = {
        "as_of": ts_now_iso(),
        "factors": {}
    }

    # Equal weights by default; front-end may renormalize
    W = {
        "naaim_exposure": 0.25,
        "fred_macro": 0.25,
        "ndx_breadth": 0.25,
        "china_proxy": 0.25,
    }

    naaim_s  = _series_of(naaim_df, col="value")
    fred_s   = None
    if fred_df is not None and not fred_df.empty:
        # If DGS10 and DFF present, convert to spread; else use first column
        cols = [c for c in fred_df.columns if c.upper() in ("DGS10","DFF","FF") or c in ("DGS10","DFF")]
        if set(["DGS10","DFF"]).issubset(fred_df.columns):
            fred_s = pd.to_numeric(fred_df["DGS10"], errors="coerce") - pd.to_numeric(fred_df["DFF"], errors="coerce")
            fred_s = fred_s.dropna()
        else:
            fred_s = _series_of(fred_df, col=fred_df.columns[-1])
    breadth_s = _series_of(breadth_df, col="pct_above_50dma")
    china_s   = _series_of(china_df, col="close")

    out["factors"]["naaim_exposure"] = make_factor("naaim_exposure", naaim_s, W["naaim_exposure"])
    out["factors"]["fred_macro"]     = make_factor("fred_macro", fred_s, W["fred_macro"])
    out["factors"]["ndx_breadth"]    = make_factor("ndx_breadth", breadth_s, W["ndx_breadth"])
    out["factors"]["china_proxy"]    = make_factor("china_proxy", china_s, W["china_proxy"])

    ensure_dir(OUT_JSON)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",",":"))

    print(f"wrote {OUT_JSON} with {len(out['factors'])} factors")

if __name__ == "__main__":
    main()
