
import os, json, pandas as pd
from tools.utils import ensure_dir, to_json_ready, ts_now_iso

OUT_FACT = "docs/factors_namm50.json"

def main():
    out = {"as_of": ts_now_iso(), "factors": {}}
    if os.path.exists("data/raw/naaim_exposure.csv"):
        na = pd.read_csv("data/raw/naaim_exposure.csv", parse_dates=["date"]).set_index("date").sort_index()
        out["factors"]["naaim_exposure"] = {
            "latest": float(na.iloc[-1,0]),
            "series": to_json_ready(na, [na.columns[0]])
        }
    if os.path.exists("data/raw/ndx_breadth_topn.csv"):
        br = pd.read_csv("data/raw/ndx_breadth_topn.csv", parse_dates=["date"]).set_index("date").sort_index()
        col = br.columns[0]
        out["factors"]["ndx_breadth"] = {
            "latest": float(br.iloc[-1,0]),
            "series": to_json_ready(br, [col])
        }
    if os.path.exists("data/raw/china_fxi.csv"):
        fx = pd.read_csv("data/raw/china_fxi.csv", parse_dates=["date"]).set_index("date").sort_index()
        out["factors"]["china_proxy"] = {
            "latest": float(fx.iloc[-1,0]),
            "series": to_json_ready(fx, [fx.columns[0]])
        }
    if os.path.exists("data/raw/fred_bundle.csv"):
        fr = pd.read_csv("data/raw/fred_bundle.csv", parse_dates=["date"]).set_index("date").sort_index()
        cols = list(fr.columns)[:3]
        out["factors"]["fred_macro"] = {
            "columns": cols,
            "series": to_json_ready(fr, cols)
        }
    ensure_dir(OUT_FACT)
    with open(OUT_FACT, "w") as f:
        json.dump(out, f, indent=2)
    print("Wrote", OUT_FACT)

if __name__ == "__main__":
    main()
