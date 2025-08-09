
import os, json, math, time, io, re, datetime as dt
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

def ts_now_iso():
    return pd.Timestamp.utcnow().isoformat(timespec="seconds")+"Z"

def to_json_ready(df: pd.DataFrame, cols=None):
    if cols is None:
        cols = list(df.columns)
    out = []
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
            if isinstance(v, (np.floating, float)) and not (pd.isna(v) or np.isnan(v)):
                v = float(v)
            item.append(v)
        out.append(item)
    return out

def zscore(s: pd.Series):
    s = pd.Series(s, dtype=float)
    m = s.mean(); sd = s.std(ddof=0)
    if sd == 0 or pd.isna(sd):
        return pd.Series(np.zeros(len(s), dtype=float), index=s.index)
    return (s - m) / sd

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
