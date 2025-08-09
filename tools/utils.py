
import os, io, json, math, time, re
from typing import List, Dict, Any
import numpy as np
import pandas as pd

def ts_now_iso():
    try:
        return pd.Timestamp.utcnow().isoformat(timespec="seconds") + "Z"
    except Exception:
        return str(pd.Timestamp.utcnow())

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def zscore(s: pd.Series, ddof: int = 0) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").astype(float)
    m = s.mean()
    sd = s.std(ddof=ddof)
    if sd == 0 or pd.isna(sd):
        return pd.Series([0.0]*len(s), index=s.index)
    return (s - m) / sd

def rolling_sharpe(returns: pd.Series, win: int = 252) -> pd.Series:
    r = pd.to_numeric(returns, errors="coerce").astype(float).fillna(0.0)
    mu = r.rolling(win).mean()
    sd = r.rolling(win).std(ddof=0)
    sharpe = np.where(sd==0, 0.0, (mu / sd) * np.sqrt(252))
    return pd.Series(sharpe, index=r.index)

def to_json_ready(df: pd.DataFrame, cols=None, weight: float = 0.25):
    if df is None or df.empty:
        return []
    if cols is None:
        cols = [df.columns[-1]]
    col = cols[0]
    out = []
    for ts, v in df[col].items():
        if isinstance(ts, (pd.Timestamp, np.datetime64)):
            t = pd.Timestamp(ts).strftime("%Y-%m-%d")
        else:
            t = str(ts)
        try:
            val = None if (pd.isna(v) or np.isnan(v)) else float(v)
        except Exception:
            val = None
        out.append([t, val, round(float(weight), 4)])
    return out
