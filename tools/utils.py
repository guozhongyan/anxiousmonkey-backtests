import os, json, time, datetime as dt
from typing import List, Dict
import pandas as pd
import numpy as np

__all__ = [
    "ensure_dir",
    "ts_now_iso",
    "to_json_ready",
    "zscore",
    "rolling_sharpe",
]

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def ts_now_iso():
    # UTC timestamp in ISO8601 ending with Z
    return pd.Timestamp.utcnow().isoformat(timespec="seconds") + "Z"

def to_json_ready(df: pd.DataFrame, cols=None):
    if df is None or df.empty:
        return []
    if cols is None:
        cols = list(df.columns)
    out: List[list] = []
    for idx, row in df[cols].iterrows():
        if isinstance(idx, (pd.Timestamp, np.datetime64)):
            ts = pd.Timestamp(idx).strftime("%Y-%m-%d")
        else:
            ts = str(idx)
        item = [ts]
        for c in cols:
            v = row[c]
            if isinstance(v, (np.floating, float)):
                if pd.isna(v) or np.isnan(v):
                    v = None
            if isinstance(v, (np.integer, int)):
                v = int(v)
            item.append(v)
        out.append(item)
    return out

def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").astype(float)
    m = s.mean()
    sd = s.std(ddof=0)
    if pd.isna(sd) or sd == 0:
        return pd.Series(np.zeros(len(s), dtype=float), index=s.index)
    return (s - m) / sd

def rolling_sharpe(rets: pd.Series, window: int = 63, ann_factor: int = 252) -> pd.Series:
    """Rolling Sharpe ratio with population std to avoid small-sample blowups."""
    r = pd.to_numeric(rets, errors="coerce").astype(float).fillna(0.0)
    roll_mean = r.rolling(window).mean()
    roll_std = r.rolling(window).std(ddof=0).replace(0, np.nan)
    sharpe = (roll_mean / roll_std) * (ann_factor ** 0.5)
    return sharpe.fillna(0.0)
