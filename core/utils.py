
import os, json
import pandas as pd
import numpy as np

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

def ts_now_iso():
    return pd.Timestamp.utcnow().isoformat(timespec="seconds") + "Z"

def to_json_ready(df: pd.DataFrame, ts_col=None, val_col=None):
    if df is None or df.empty:
        return []
    if ts_col is None:
        ts_col = df.columns[0]
    if val_col is None:
        val_col = df.columns[-1]
    out = []
    for _, row in df[[ts_col, val_col]].iterrows():
        ts = pd.to_datetime(row[ts_col]).strftime("%Y-%m-%d")
        v = row[val_col]
        if isinstance(v, (np.floating, float)):
            v = None if pd.isna(v) else float(v)
        if isinstance(v, (np.integer, int)):
            v = int(v)
        out.append([ts, None, v])
    return out

def write_json(path: str, obj: dict):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
