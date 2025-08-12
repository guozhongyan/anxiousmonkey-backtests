# --- repo path bootstrap (CI/CLI 双保险) ---
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
THIS = os.path.dirname(__file__)
if THIS in sys.path:
    sys.path.remove(THIS)
# ------------------------------------------

import json

try:
    from core.utils import ts_now_iso, write_json
except Exception:
    from tools.utils import ts_now_iso, write_json

IN = "docs/factors_namm50.json"
OUT = "docs/models/namm50.json"
DEF = {
    "NAAM": 0.70,
    "FRED": 0.20,
    "NDX50": 0.05,
    "CHINA": 0.05,
    "VIXCLS": 0.0,
    "CURVE10Y2Y": 0.0,
    "CURVE10Y3M": 0.0,
    "DGS10": 0.0,
    "DFF": 0.0,
    "DFII10": 0.0,
    "UNRATE": 0.0,
    "CPIAUCSL": 0.0,
    "BAMLH0A0HYM2": 0.0,
    "MOMQQQ12M1M": 0.0,
    "RSIQQQ14": 0.0,
    "RSISPY14": 0.0,
    "ATRQQQ14": 0.0,
}

FACT_MAP = {
    "naaim_exposure": "NAAM",
    "fred_macro": "FRED",
    "ndx_breadth": "NDX50",
    "china_proxy": "CHINA",
    "vix_cls": "VIXCLS",
    "curve_10y2y": "CURVE10Y2Y",
    "curve_10y3m": "CURVE10Y3M",
    "dgs10": "DGS10",
    "dff": "DFF",
    "dfii10": "DFII10",
    "unrate": "UNRATE",
    "cpiaucsl": "CPIAUCSL",
    "baml_hy_oas": "BAMLH0A0HYM2",
    "mom_qqq_12m1m": "MOMQQQ12M1M",
    "rsi_qqq_14": "RSIQQQ14",
    "rsi_spy_14": "RSISPY14",
    "atr_qqq_14": "ATRQQQ14",
}


def main():
    try:
        fx = json.load(open(IN, "r", encoding="utf-8"))
    except Exception:
        fx = {"factors": {}}
    present = {key: 1.0 if fx.get("factors", {}).get(fid, {}).get("series") else 0.0 for fid, key in FACT_MAP.items()}
    core_keys = ["NAAM", "FRED", "NDX50", "CHINA"]
    if sum(present[k] for k in core_keys) == 0:
        weights = {"NAAM": 1.0, "FRED": 0.0, "NDX50": 0.0, "CHINA": 0.0}
    else:
        pool = {k: DEF[k] for k in core_keys if present.get(k, 0) > 0}
        s = sum(pool.values()) or 1.0
        weights = {k: round(v / s, 4) for k, v in pool.items()}
    for k in DEF.keys():
        weights.setdefault(k, 0.0)
    payload = {"as_of": ts_now_iso(), "model": "NAMM-50", "version": "v0.2.0", "weights": weights}
    write_json(OUT, payload)
    print(f"wrote {OUT}: {payload}")


if __name__ == "__main__":
    main()
