import os, io, re, json, time, math, datetime as dt
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

# ============ Existing helpers ============
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
                if pd.isna(v) or (isinstance(v, float) and math.isnan(v)):
                    v = None
            if isinstance(v, (np.integer, int)):
                v = int(v)
            item.append(v)
        out.append(item)
    return out

def zscore(s: pd.Series):
    s = s.astype(float)
    m, sd = s.mean(), s.std(ddof=0)
    if sd == 0 or pd.isna(sd):
        return pd.Series(np.zeros(len(s),dtype=float), index=s.index)
    return (s - m) / sd

def label_from_score(x: float, thr_on=0.5, thr_off=-0.5):
    if pd.isna(x):
        return "Neutral"
    if x >= thr_on: return "Risk-On"
    if x <= thr_off: return "Risk-Off"
    return "Neutral"

def ensure_dir(path: str):
    d = os.path.dirname(path) if os.path.splitext(path)[1] else path
    if d:
        os.makedirs(d, exist_ok=True)

# ============ New robust IO helpers ============
import requests

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AMBot/1.0; +https://github.com/guozhongyan/anxiousmonkey-backtests)",
    "Accept": "text/html,application/json,application/xml;q=0.9,*/*;q=0.8"
}

def _http_get(url: str, timeout=30):
    r = requests.get(url, headers=_DEFAULT_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r

def wayback_lookup(url: str) -> Optional[str]:
    try:
        api = f"https://archive.org/wayback/available?url={url}"
        r = _http_get(api, timeout=20)
        js = r.json()
        snap = js.get("archived_snapshots", {}).get("closest")
        if snap and snap.get("available") and snap.get("url"):
            return snap["url"]
    except Exception:
        return None
    return None

def get_text_with_fallbacks(urls: List[str], timeout=30) -> Optional[str]:
    last_err = None
    for u in urls:
        try:
            return _http_get(u, timeout=timeout).text
        except Exception as e:
            last_err = e
            # try wayback for this url
            try:
                wb = wayback_lookup(u)
                if wb:
                    return _http_get(wb, timeout=timeout).text
            except Exception as e2:
                last_err = e2
    # print last error context for logs
    if last_err:
        print(f"[warn] all sources failed: {last_err}")
    return None

def safe_read_csv_text(text: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(io.StringIO(text))
    except Exception as e:
        print("[warn] read_csv failed:", e)
        return None

def safe_write_csv(df: pd.DataFrame, path: str):
    ensure_dir(path)
    df.to_csv(path, index=False)

def write_placeholder_csv(path: str, headers: List[str]):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")

def load_prev_csv(path: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(path)
    except Exception:
        return None

def json_dump(obj, path: str):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), indent=None)
