import os, json
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "data" / "raw"
DOCS = REPO_ROOT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

FACTORS_JSON = DOCS / "factors_namm50.json"

def utc_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def read_csv_series(path: Path, value_col=None):
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if value_col and value_col in df.columns:
            s = df[value_col]
            # optional date column normalization
            dt_col = None
            for c in df.columns:
                if "date" in c.lower():
                    dt_col = c; break
            if dt_col:
                idx = pd.to_datetime(df[dt_col]).dt.strftime("%Y-%m-%d").tolist()
            else:
                idx = list(range(len(s)))
            return [[str(idx[i]), None, float(s.iloc[i])] for i in range(len(s)) if pd.notna(s.iloc[i])]
        else:
            # assume last column is the numeric metric
            last = df.columns[-1]
            s = df[last]
            idx = list(range(len(s)))
            return [[str(idx[i]), None, float(s.iloc[i])] for i in range(len(s)) if pd.notna(s.iloc[i])]
    except Exception as e:
        print(f"read_csv_series({path}): {e}")
        return None

def main():
    out = {"as_of": utc_iso(), "factors": {}}

    # 1) NAAIM
    out["factors"]["naaim_exposure"] = {
        "series": read_csv_series(RAW / "naaim_exposure.csv")
    }

    # 2) FRED Macro (two columns expected DGS10, DFF) -> store last row as pair, also whole series of DGS10
    fred_path = RAW / "fred_namm50.csv"
    if fred_path.exists():
        try:
            df = pd.read_csv(fred_path)
            # Store DGS10 as series for chart
            if "DGS10" in df.columns:
                out["factors"].setdefault("fred_macro", {})["series"] = [[str(i), None, float(v)] for i, v in enumerate(df["DGS10"]) if pd.notna(v)]
        except Exception as e:
            print("fred read error", e)

    # 3) NDX breadth (>50DMA)
    out["factors"]["ndx_breadth"] = {
        "series": read_csv_series(RAW / "ndx_breadth_topn.csv")
    }

    # 4) China proxy (FXI or alike)
    out["factors"]["china_proxy"] = {
        "series": read_csv_series(RAW / "china_proxy_fxi.csv")
    }

    # keep existing file if new series all None
    if all(v.get("series") is None for v in out["factors"].values()):
        if FACTORS_JSON.exists():
            print("No new series. Keeping previous file.")
            return

    tmp = FACTORS_JSON.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    tmp.replace(FACTORS_JSON)
    print(f"wrote {FACTORS_JSON}")

if __name__ == "__main__":
    main()