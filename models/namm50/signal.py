import json, numpy as np, pandas as pd
from core.utils import ts_now_iso, write_json

MODEL = "docs/models/namm50.json"
FACT  = "docs/factors_namm50.json"
OUT   = "docs/signals_namm50.json"
WINDOW = 180

WEIGHT_MAP = {
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


def extract_values(series):
    vals = []
    for row in series:
        if not row:
            continue
        value = None
        if len(row) > 1 and row[1] is not None:
            value = row[1]
        elif len(row) > 2:
            value = row[2]
        if value is not None:
            vals.append(float(value))
    return pd.Series(vals) if vals else None


def compute_z(series):
    if series is None or series.empty:
        return None
    win = WINDOW if len(series) >= WINDOW else max(60, len(series))
    if win < 2:
        return None
    z = (series - series.rolling(win).mean()) / series.rolling(win).std(ddof=0)
    return z.iloc[-1] if not z.empty else None


def main():
    try:
        weights = json.load(open(MODEL, "r", encoding="utf-8")).get("weights", {})
    except Exception:
        weights = {}
    try:
        factors = json.load(open(FACT, "r", encoding="utf-8")).get("factors", {})
    except Exception:
        factors = {}
    factors_used, placeholders = [], []
    score = 0.0
    for fid, wkey in WEIGHT_MAP.items():
        w = weights.get(wkey, 0.0)
        series = factors.get(fid, {}).get("series")
        if not series:
            placeholders.append(wkey)
            continue
        vals = extract_values(series)
        z = compute_z(vals)
        if z is None or np.isnan(z):
            placeholders.append(wkey)
            continue
        score += w * float(z)
        factors_used.append(wkey)
    stance = "Risk-On" if score >= 0.5 else ("Risk-Off" if score <= -0.5 else "Neutral")
    payload = {
        "as_of": ts_now_iso(),
        "model": "NAMM-50",
        "score": float(score),
        "stance": stance,
        "details": {
            "factors_used": factors_used,
            "placeholders": placeholders,
            "window": WINDOW,
        },
    }
    write_json(OUT, payload)
    print(f"wrote {OUT}: score={score:.3f}, stance={stance}")


if __name__ == "__main__":
    main()
