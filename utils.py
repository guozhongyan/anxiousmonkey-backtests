
import os, json, math, time, datetime as dt
import pandas as pd, numpy as np

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def ts_now_iso():
    return pd.Timestamp.utcnow().isoformat(timespec="seconds") + "Z"

def to_json_ready(df: pd.DataFrame, cols=None):
    if cols is None: cols = list(df.columns)
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
                if pd.isna(v) or np.isnan(v): v = None
            if isinstance(v, (np.integer, int)): v = int(v)
            item.append(v)
        out.append(item)
    return out

def rolling_sharpe(returns, window=63):
    r = pd.Series(returns).astype(float)
    out = r.rolling(window).apply(lambda x: (np.sqrt(252)*x.mean()/(x.std(ddof=0)+1e-12)), raw=False)
    return out
