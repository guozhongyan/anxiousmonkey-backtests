import os, json, math
import pandas as pd
import numpy as np

def ts_now_iso():
    return pd.Timestamp.utcnow().isoformat(timespec="seconds") + "Z"

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def to_json_ready(df: pd.DataFrame, cols=None):
    if cols is None: cols = list(df.columns)
    out = []
    for idx, row in df[cols].iterrows():
        ts = pd.Timestamp(idx).strftime("%Y-%m-%d") if isinstance(idx, (pd.Timestamp, np.datetime64)) else str(idx)
        item = [ts]
        for c in cols:
            v = row[c]
            if isinstance(v, (np.floating, float)):
                v = None if (pd.isna(v)) else float(v)
            if isinstance(v, (np.integer, int)):
                v = int(v)
            item.append(v)
        out.append(item)
    return out

def zscore(s: pd.Series):
    s = s.astype(float)
    m = s.mean()
    sd = s.std(ddof=0)
    if sd == 0 or pd.isna(sd): 
        return pd.Series(np.zeros(len(s)), index=s.index, dtype=float)
    return (s - m) / sd

def rolling_sharpe(returns: pd.Series, rf: float = 0.0, window: int = 252):
    r = returns.astype(float) - rf/252.0
    roll = r.rolling(window)
    mu = roll.mean()
    sd = roll.std(ddof=0)
    with np.errstate(divide='ignore', invalid='ignore'):
        sr = mu / sd
    return sr

def write_json(path: str, obj):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
