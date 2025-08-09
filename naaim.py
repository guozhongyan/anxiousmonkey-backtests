
import os, requests, pandas as pd
from tools.utils import ensure_dir

OUT = "data/raw/naaim_exposure.csv"

def main():
    url = "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    cols = {c.lower().strip(): c for c in df.columns}
    date_col = None
    for cand in ["date","week","as of","as_of"]:
        for k,v in cols.items():
            if cand in k:
                date_col = v
                break
        if date_col: break
    val_col = None
    for cand in ["exposure","index","value"]:
        for k,v in cols.items():
            if cand in k and v != date_col:
                val_col = v
                break
        if val_col: break
    if date_col is None or val_col is None:
        date_col = df.columns[0]; val_col = df.columns[1]
    df = df[[date_col, val_col]].rename(columns={date_col:"date", val_col:"value"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    ensure_dir(OUT)
    df.to_csv(OUT, index=False)
    print(f"saved {OUT}, rows={len(df)}")

if __name__ == "__main__":
    main()
