import os, sys, json
import pandas as pd
import numpy as np

# Local package path for GitHub Actions
CUR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CUR, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.utils import ensure_dir, to_json_ready, zscore, ts_now_iso

OUT_JSON = os.path.join("docs", "factors_namm50.json")

def load_csv(path, parse_dates=["date"], index_col="date"):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if parse_dates and index_col in df.columns:
        df[index_col] = pd.to_datetime(df[index_col])
        df = df.set_index(index_col).sort_index()
    return df

def build_payload():
    payload = {
        "as_of": ts_now_iso(),
        "factors": {}
    }

    # 1) NAAIM exposure
    naaim = load_csv(os.path.join("data", "raw", "naaim_exposure.csv"))
    if naaim is not None and "value" in naaim.columns:
        payload["factors"]["naaim_exposure"] = {
            "series": to_json_ready(naaim.rename(columns={"value":"naaim"})[["naaim"]]),
            "z": to_json_ready(pd.DataFrame({"z": zscore(naaim["value"])}, index=naaim.index), cols=["z"]),
            "meta": {"unit": "%", "source": "NAAIM/Nasdaq Data Link"}
        }

    # 2) FRED macro bundle (DGS10, DFF)
    fred = load_csv(os.path.join("data", "raw", "fred_namm50.csv"))
    if fred is not None:
        cols = [c for c in ["DGS10", "DFF"] if c in fred.columns]
        if cols:
            payload["factors"]["fred_macro"] = {
                "series": to_json_ready(fred[cols], cols=cols),
                "meta": {"source": "FRED", "symbols": cols}
            }

    # 3) NDX >50DMA breadth (% or count)
    ndx = load_csv(os.path.join("data", "raw", "ndx_breadth_topn.csv"))
    if ndx is not None:
        col = "pct_above_50dma" if "pct_above_50dma" in ndx.columns else ndx.columns[-1]
        payload["factors"]["ndx_breadth"] = {
            "series": to_json_ready(ndx.rename(columns={col:"pct"})[["pct"]], cols=["pct"]),
            "meta": {"note": "Computed from Yahoo; may be rate-limited."}
        }

    # 4) China proxy (FXI or CN50)
    ch = load_csv(os.path.join("data", "raw", "china_proxy_fxi.csv"))
    if ch is not None:
        col = "close" if "close" in ch.columns else ch.columns[-1]
        payload["factors"]["china_proxy"] = {
            "series": to_json_ready(ch.rename(columns={col:"price"})[["price"]], cols=["price"]),
            "meta": {"symbol": "FXI"}
        }

    return payload

def main():
    ensure_dir(OUT_JSON)
    payload = build_payload()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"wrote {OUT_JSON} with keys: {list(payload['factors'].keys())}")

if __name__ == "__main__":
    main()
