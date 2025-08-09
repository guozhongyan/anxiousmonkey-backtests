
import os, sys, json
import pandas as pd, numpy as np
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.utils import ensure_dir, ts_now_iso, to_json_ready

NAAIM_CSV = "data/raw/naaim_exposure.csv"
FRED_CSV  = "data/raw/fred_namm50.csv"
BREADTH_CSV = "data/raw/ndx_breadth_topn.csv"
CHINA_CSV = "data/raw/china_proxy_fxi.csv"
OUT_JSON = "docs/factors_namm50.json"

def load_csv(path: str):
    if not os.path.exists(path): return None
    try:
        df = pd.read_csv(path, parse_dates=[0], index_col=0)
        if df is None or df.empty: return None
        return df
    except Exception:
        return None

def build_payload():
    payload = {"as_of": ts_now_iso(), "factors": {}}

    naaim = load_csv(NAAIM_CSV)
    if naaim is not None:
        # expect column 'value' or single column
        if "value" not in naaim.columns:
            naaim.columns = ["value"]
        payload["factors"]["naaim_exposure"] = {
            "name": "NAAIM Exposure Index",
            "weight": 0.25,
            "series": to_json_ready(naaim, ["value"], weight=0.25)
        }

    fred = load_csv(FRED_CSV)
    if fred is not None:
        # produce macro proxy; if both present, use DGS10 - DFF as level
        macro = fred.copy()
        if "DGS10" in macro.columns and "DFF" in macro.columns:
            macro["macro"] = pd.to_numeric(macro["DGS10"], errors="coerce") - pd.to_numeric(macro["DFF"], errors="coerce")
        else:
            macro["macro"] = pd.to_numeric(macro[macro.columns[-1]], errors="coerce")
        payload["factors"]["fred_macro"] = {
            "name": "FRED Macro (10Y-FF)",
            "weight": 0.25,
            "series": to_json_ready(macro[["macro"]], ["macro"], weight=0.25)
        }

    breadth = load_csv(BREADTH_CSV)
    if breadth is not None:
        if "pct_above_50dma" not in breadth.columns:
            breadth.columns = ["pct_above_50dma"]
        payload["factors"]["ndx_breadth"] = {
            "name": ">50DMA Breadth (NDX)",
            "weight": 0.25,
            "series": to_json_ready(breadth, ["pct_above_50dma"], weight=0.25)
        }

    china = load_csv(CHINA_CSV)
    if china is not None:
        if "close" not in china.columns:
            china.columns = ["close"]
        payload["factors"]["china_proxy"] = {
            "name": "China Proxy (FXI)",
            "weight": 0.25,
            "series": to_json_ready(china, ["close"], weight=0.25)
        }

    return payload

def main():
    data = build_payload()
    ensure_dir(OUT_JSON)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT_JSON} with keys: {list(data.get('factors',{}).keys())}")

if __name__ == "__main__":
    main()
