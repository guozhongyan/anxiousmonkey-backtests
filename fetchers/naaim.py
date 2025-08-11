import os, io, time, requests, pandas as pd
from core.utils import ensure_dir

CSV_URL = "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv"
OUT = "data/raw/naaim_exposure.csv"

def main():
    ok = False
    try:
        r = requests.get(CSV_URL, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        date_col = next((c for c in df.columns if 'date' in c.lower()), df.columns[0])
        val_col  = next((c for c in df.columns if 'exposure' in c.lower() or 'value' in c.lower()), df.columns[-1])
        df = df[[date_col, val_col]].rename(columns={date_col:"date", val_col:"value"})
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")
        ensure_dir(OUT)
        df.to_csv(OUT, index=False)
        print(f"saved {OUT}, rows={len(df)}")
        ok = True
    except Exception as e:
        print(f"NAAIM primary failed: {e}")
    if not ok:
        if os.path.exists(OUT):
            print("placeholder: keep existing file")
        else:
            ensure_dir(OUT)
            pd.DataFrame([{"date": pd.Timestamp.today().normalize(), "value": None}]).to_csv(OUT, index=False)
            print("wrote placeholder NAAIM file")
if __name__ == "__main__":
    main()
