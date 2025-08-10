
# -*- coding: utf-8 -*-
"""
NAAIM Exposure Index fetcher — robust hotfix.

What it does:
  1) Tries the official CSV URL(s).
  2) If 404/timeout, falls back to Wayback closest snapshot.
  3) If still unavailable, keeps previous CSV if exists;
     otherwise writes a schema-correct placeholder so downstream won't crash.

Output:
  data/raw/naaim_exposure.csv  (columns: date,value)

Safe to drop in: fetchers/naaim.py
"""

import os, io, time, json
from typing import Optional, Tuple
import requests
import pandas as pd

OUT_CSV = "data/raw/naaim_exposure.csv"

CANDIDATE_URLS = [
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
]
WAYBACK_API = (
    "https://archive.org/wayback/available?url="
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv"
)

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def _try_download(url: str, timeout: int = 25) -> Optional[str]:
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200 and r.content and len(r.content) > 50:
            print(f"naaim: {url} -> HTTP 200, {len(r.content)} bytes")
            return r.text
        print(f"naaim: {url} -> HTTP {r.status_code}")
    except Exception as e:
        print(f"naaim: {url} -> error: {e}")
    return None

def _fetch_wayback() -> Tuple[Optional[str], Optional[str]]:
    try:
        r = requests.get(WAYBACK_API, timeout=20)
        r.raise_for_status()
        data = r.json()
        snap = data.get("archived_snapshots", {}).get("closest", {})
        if snap.get("available"):
            archived_url = snap.get("url")
            txt = _try_download(archived_url, timeout=25)
            if txt:
                print(f"naaim: using Wayback snapshot: {archived_url}")
                return txt, archived_url
        print("naaim: no Wayback snapshot available")
    except Exception as e:
        print(f"naaim: wayback api error: {e}")
    return None, None

def _parse_csv(text: str) -> pd.DataFrame:
    # Be generous about headers
    df = pd.read_csv(io.StringIO(text))
    df.columns = [str(c).strip().lower() for c in df.columns]
    # Guess columns
    date_col = None
    for key in ["date", "week", "asof", "as_of"]:
        date_col = next((c for c in df.columns if key in c), None)
        if date_col:
            break
    if date_col is None:
        date_col = df.columns[0]

    val_col = None
    for key in ["exposure", "index", "value", "naaim"]:
        val_col = next((c for c in df.columns if key in c), None)
        if val_col:
            break
    if val_col is None:
        val_col = df.columns[-1]

    out = df[[date_col, val_col]].copy()
    out.columns = ["date", "value"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    return out

def write_placeholder():
    ensure_dir(OUT_CSV)
    # Minimal header to keep downstream stable
    pd.DataFrame(columns=["date","value"]).to_csv(OUT_CSV, index=False)
    print("naaim: wrote placeholder CSV (empty dataframe)")

def main():
    ensure_dir(OUT_CSV)

    # 1) direct candidates
    text = None
    used_url = None
    for url in CANDIDATE_URLS:
        text = _try_download(url)
        if text:
            used_url = url
            break

    # 2) wayback fallback
    if text is None:
        text, used_url = _fetch_wayback()

    if text is not None:
        try:
            df = _parse_csv(text)
            if len(df) > 0:
                df.to_csv(OUT_CSV, index=False)
                print(f"saved {OUT_CSV}, rows={len(df)} (source: {used_url})")
                return
            else:
                print("naaim: parsed dataframe empty; will fallback")
        except Exception as e:
            print(f"naaim: parse error -> {e}; will fallback")

    # 3) keep previous file if exists
    if os.path.exists(OUT_CSV):
        try:
            old = pd.read_csv(OUT_CSV)
            print(f"naaim: using previous CSV, rows={len(old)}")
            return
        except Exception as e:
            print(f"naaim: previous CSV unreadable -> {e}")

    # 4) last resort: placeholder
    write_placeholder()

if __name__ == "__main__":
    main()
