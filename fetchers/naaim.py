import os, sys, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import get_text_with_fallbacks, safe_read_csv_text, safe_write_csv, write_placeholder_csv, load_prev_csv

OUT_CSV = "data/raw/naaim_exposure.csv"

URLS = [
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
]

def main():
    txt = get_text_with_fallbacks(URLS, timeout=30)
    if txt:
        df = safe_read_csv_text(txt)
        if df is not None:
            # 标准化两列
            cols = [c.lower() for c in df.columns]
            if "date" not in cols or ("value" not in cols and "exposure" not in cols):
                # 兼容官方 csv 的列名大小写
                df.columns = [c.lower() for c in df.columns]
            if "value" not in df.columns and "exposure" in df.columns:
                df["value"] = df["exposure"]
            if "date" in df.columns and "value" in df.columns:
                df = df[["date", "value"]].dropna()
                safe_write_csv(df, OUT_CSV)
                print(f"saved {OUT_CSV}, rows={len(df)}")
                return
    # 兜底：沿用旧文件
    prev = load_prev_csv(OUT_CSV)
    if prev is not None and len(prev) > 0:
        safe_write_csv(prev, OUT_CSV)
        print(f"[fallback] kept previous file: {OUT_CSV}, rows={len(prev)}")
        return
    # 占位
    write_placeholder_csv(OUT_CSV, ["date","value"])
    print(f"[placeholder] wrote empty {OUT_CSV}")

if __name__ == "__main__":
    main()
