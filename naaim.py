# -*- coding: utf-8 -*-
"""
Robust NAAIM Exposure Index fetcher.
Saves to: data/raw/naaim_exposure.csv
"""
import os, io, sys
from typing import Optional, List
import requests
import pandas as pd

OUT_CSV = "data/raw/naaim_exposure.csv"
SEED_CSV = "seed/naaim_exposure_seed.csv"

PRIMARY_URLS = [
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
]

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

def fetch(url: str, timeout: int = 30) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text

def parse_csv(text: str) -> Optional[pd.DataFrame]:
    try:
        df = pd.read_csv(io.StringIO(text))
    except Exception:
        try:
            tables = pd.read_html(text)
            df = tables[0] if tables else None
        except Exception:
            df = None
    if df is None or df.empty:
        return None
    # normalize
    cols = [str(c).strip() for c in df.columns]
    lower = [c.lower() for c in cols]
    df.columns = lower
    date_col = next((c for c in lower if "date" in c), None) or lower[0]
    val_col = next((c for c in lower if any(k in c for k in ("exposure","value","naaim"))), None) or (lower[1] if len(lower)>1 else lower[0])
    if date_col not in df.columns or val_col not in df.columns:
        return None
    out = df[[date_col, val_col]].copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    out[val_col] = pd.to_numeric(out[val_col], errors="coerce")
    out = out.dropna().sort_values(date_col)
    out.columns = ["date", "value"]
    return out

def try_sources(urls: List[str]) -> Optional[pd.DataFrame]:
    for u in urls:
        try:
            txt = fetch(u)
            df = parse_csv(txt)
            if df is not None and not df.empty:
                print(f"[ok] parsed NAAIM from {u}, rows={len(df)}")
                return df
            else:
                print(f"[warn] parsed empty/invalid from {u}")
        except Exception as e:
            print(f"[warn] fetch failed {u}: {e}")
    return None

def main():
    mirrors_env = os.getenv("NAAIM_MIRROR_URLS", "").strip()
    mirrors = [s.strip() for s in mirrors_env.split(",") if s.strip()] if mirrors_env else []
    urls = PRIMARY_URLS + mirrors
    df = try_sources(urls)
    if df is not None:
        ensure_dir(OUT_CSV)
        df.to_csv(OUT_CSV, index=False)
        print(f"saved {OUT_CSV}, rows={len(df)}")
        return 0
    if os.path.exists(OUT_CSV):
        print("fetch failed; keep previous file.")
        return 0
    if os.path.exists(SEED_CSV):
        ensure_dir(OUT_CSV)
        pd.read_csv(SEED_CSV).to_csv(OUT_CSV, index=False)
        print(f"seeded {OUT_CSV} from {SEED_CSV}")
        return 0
    ensure_dir(OUT_CSV)
    pd.DataFrame(columns=["date","value"]).to_csv(OUT_CSV, index=False)
    print(f"wrote empty placeholder {OUT_CSV}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
