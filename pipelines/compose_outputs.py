import os, json, pandas as pd, numpy as np
from core.utils import ensure_dir, ts_now_iso

RAW = {
    "naaim_exposure": "data/raw/naaim_exposure.csv",
    "fred_bundle": "data/raw/fred_bundle.csv",
    "ndx_breadth": "data/raw/ndx_breadth_50dma.csv",
    "china_proxy": "data/raw/china_proxy_fxi.csv",
    "prices": "docs/prices.json",
}
OUT = "docs/factors_namm50.json"


def load_naaim(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["date"]).dropna(subset=["date"]).set_index("date").sort_index()
    if "value" not in df.columns:
        return None
    return pd.DataFrame({"value": df["value"].astype(float)})


def load_fred_macro(df):
    if df is None or not {"DGS10", "DFF"}.issubset(df.columns):
        return None
    val = df["DGS10"].astype(float) - df["DFF"].astype(float)
    return pd.DataFrame({"value": val})


def load_ndx(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    col = "pct_above" if "pct_above" in df.columns else df.columns[-1]
    return pd.DataFrame({"value": df[col].astype(float)})


def load_china(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    if "close" not in df.columns:
        return None
    return pd.DataFrame({"value": df["close"].astype(float)})


def load_fred_bundle(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def load_prices(path):
    try:
        js = json.load(open(path, "r", encoding="utf-8"))
        series = js.get("series", {})
        frames = {}
        for t, arr in series.items():
            idx = [pd.to_datetime(a[0]) for a in arr]
            vals = [a[1] for a in arr]
            frames[t] = pd.Series(vals, index=idx, dtype=float)
        if frames:
            return pd.DataFrame(frames).sort_index()
    except Exception:
        pass
    return None


def price_factor(s, transform):
    if transform == "mom_12m_1m":
        return s.pct_change(252) - s.pct_change(21)
    if transform == "rsi_14":
        delta = s.diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = (-delta.clip(upper=0)).rolling(14).mean()
        rs = up / down
        return 100 - (100 / (1 + rs))
    if transform == "atrp_14":
        tr = s.diff().abs()
        atr = tr.rolling(14).mean()
        return atr / s * 100.0
    return None


def df_to_series(df):
    if df is None or df.empty:
        return None
    out = []
    for idx, val in df["value"].items():
        ts = idx.strftime("%Y-%m-%d")
        v = None if pd.isna(val) else float(val)
        out.append([ts, None, v])
    return out


def main():
    reg = json.load(open("factor_registry.yml", "r", encoding="utf-8"))
    fred_df = load_fred_bundle(RAW["fred_bundle"])
    px = load_prices(RAW["prices"])
    payload = {"as_of": ts_now_iso(), "factors": {}}

    payload["factors"]["naaim_exposure"] = {"series": df_to_series(load_naaim(RAW["naaim_exposure"]))}
    payload["factors"]["fred_macro"] = {"series": df_to_series(load_fred_macro(fred_df))}
    payload["factors"]["ndx_breadth"] = {"series": df_to_series(load_ndx(RAW["ndx_breadth"]))}
    payload["factors"]["china_proxy"] = {"series": df_to_series(load_china(RAW["china_proxy"]))}

    extra = 0
    for fid, spec in reg.get("factors", {}).items():
        if fid in payload["factors"]:
            continue
        if spec.get("source") == "fred":
            code = spec.get("code")
            if fred_df is not None and code in fred_df.columns:
                s = fred_df[code].astype(float)
                payload["factors"][fid] = {"series": df_to_series(s.to_frame("value"))}
            else:
                payload["factors"][fid] = {"series": None}
            extra += 1
        elif spec.get("source") == "prices":
            ticker = spec.get("ticker")
            transform = spec.get("transform")
            if px is not None and ticker in px.columns:
                s = price_factor(px[ticker], transform)
                payload["factors"][fid] = {"series": df_to_series(s.to_frame("value")) if s is not None else None}
            else:
                payload["factors"][fid] = {"series": None}
            extra += 1
    ensure_dir(OUT)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT} with keys: {list(payload['factors'].keys())}; added {extra} extra factors")


if __name__ == "__main__":
    main()
