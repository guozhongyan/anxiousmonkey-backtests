
import os, io, time, json, sys, traceback
from datetime import datetime
import pandas as pd
import numpy as np
import requests

# Ensure repo root is importable when run as a script or via runpy
ROOT = os.path.abspath(os.getcwd())
sys.path.insert(0, ROOT)

OUT_CSV = os.environ.get("AM_NAAIM_OUT", "data/raw/naaim_exposure.csv")

CANDIDATE_URLS = [
    "https://www.naaim.org/wp-content/uploads/naaim-exposure-index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://naaim.org/wp-content/uploads/naaim-exposure-index.csv",
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
]

PAGE_URL = "https://www.naaim.org/naaim-exposure-index/"

def _download_csv(url, timeout=30):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200 and len(r.content) > 64:
            return r.content
    except Exception:
        pass
    return None

def _parse_page(url=PAGE_URL, timeout=30):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        # Try read first table
        tables = pd.read_html(r.text)
        if not tables:
            return None
        # Heuristic: find table that has 2 columns and looks like Date/Exposure
        for df in tables:
            if df.shape[1] >= 2:
                # Normalize column names
                cols = [str(c).strip().lower() for c in df.columns]
                df.columns = cols
                # find date column
                date_col = next((c for c in cols if "date" in c), cols[0])
                # find exposure column
                exp_col = next((c for c in cols if "exposure" in c or "index" in c or "value" in c or "naaim" in c), cols[-1])
                series = df[[date_col, exp_col]].dropna()
                series.columns = ["date", "exposure"]
                return series
    except Exception:
        pass
    return None

def clean_and_save(df: pd.DataFrame, out_path: str):
    df = df.copy()
    # Normalize date
    def to_date(x):
        try:
            return pd.to_datetime(x).date()
        except Exception:
            return pd.NaT
    if "date" not in df.columns:
        # Try infer
        df.columns = ["date", "exposure"]
    df["date"] = df["date"].apply(to_date)
    df = df.dropna(subset=["date"])
    # exposure numeric
    df["exposure"] = pd.to_numeric(df["exposure"], errors="coerce")
    df = df.dropna(subset=["exposure"])
    df = df.sort_values("date")
    # save
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"saved {out_path}, rows={len(df)}")

def main():
    # 1) Try direct CSVs (several file name variants NAAIM has used historically)
    for url in CANDIDATE_URLS:
        blob = _download_csv(url)
        if blob:
            # Try parse quickly
            try:
                df = pd.read_csv(io.BytesIO(blob))
            except Exception:
                try:
                    df = pd.read_csv(io.BytesIO(blob), header=None)
                    if df.shape[1] >= 2:
                        df = df.iloc[:, :2]
                        df.columns = ["date", "exposure"]
                except Exception:
                    df = None
            if isinstance(df, pd.DataFrame) and df.shape[1] >= 2:
                if "date" not in df.columns or "exposure" not in df.columns:
                    # attempt standardization
                    cols = [str(c).strip().lower() for c in df.columns]
                    df.columns = cols
                    # pick first two
                    if "date" not in df.columns or "exposure" not in df.columns:
                        df = df.iloc[:, :2]
                        df.columns = ["date", "exposure"]
                clean_and_save(df[["date","exposure"]], OUT_CSV)
                return
    # 2) Parse the page if CSV not found
    df = _parse_page()
    if isinstance(df, pd.DataFrame) and not df.empty:
        clean_and_save(df, OUT_CSV)
        return

    # 3) Fallback: soft-fail with placeholder (so the pipeline can continue)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    placeholder = pd.DataFrame({"date": [], "exposure": []})
    placeholder.to_csv(OUT_CSV, index=False)
    print("[warn] NAAIM data not available from free sources; wrote empty CSV placeholder:", OUT_CSV)

if __name__ == "__main__":
    main()
