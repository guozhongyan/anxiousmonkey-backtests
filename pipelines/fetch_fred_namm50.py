\
    import os, json, time
    import pandas as pd
    import numpy as np
    import requests
    from tools.utils import zscore, label_from_score, ensure_dir

    OUT_FACTORS = "data/raw/namm50_components.csv"
    OUT_SCORE = "data/raw/namm50_score.csv"
    API_KEY = os.environ.get("FRED_API_KEY","").strip()

    SERIES = {
        "DGS10": {"freq":"D"},
        "DGS2": {"freq":"D"},
        "T10Y3M": {"freq":"D"},
        "CPIAUCSL": {"freq":"M"},
        "INDPRO": {"freq":"M"},
        "UNRATE": {"freq":"M"},
        "BAMLH0A0HYM2": {"freq":"D"},
        "STLFSI2": {"freq":"W"},
        "VIXCLS": {"freq":"D"},
        "DTWEXBGS": {"freq":"D"},
        "DCOILWTICO": {"freq":"D"}
    }

    def fred_series(series_id, observation_start="1990-01-01"):
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = dict(
            api_key=API_KEY,
            file_type="json",
            series_id=series_id,
            observation_start=observation_start
        )
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        j = r.json()
        obs = j.get("observations", [])
        df = pd.DataFrame(obs)
        if df.empty:
            return pd.Series(dtype=float)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.set_index("date")["value"].sort_index()

    def align_daily(s):
        s = s.copy()
        s.index = pd.to_datetime(s.index)
        daily = pd.date_range(s.index.min(), s.index.max(), freq="B")
        return s.reindex(daily).ffill()

    def compute_namm50(df: pd.DataFrame):
        feats = {}
        feats["curve_10y3m_z"] = zscore(df["T10Y3M"])
        feats["real_rate_proxy_z"] = zscore(df["DGS10"] - df["CPIAUCSL"].pct_change(12)*100.0)
        feats["indpro_mom_z"] = zscore(df["INDPRO"].pct_change(1))
        feats["unrate_inv_z"] = zscore(-df["UNRATE"])
        feats["hy_ois_z"] = zscore(-df["BAMLH0A0HYM2"])
        feats["stlfsi_inv_z"] = zscore(-df["STLFSI2"])
        feats["vix_inv_z"] = zscore(-df["VIXCLS"])
        feats["dxy_inv_z"] = zscore(-df["DTWEXBGS"])
        feats["wti_z"] = zscore(df["DCOILWTICO"].pct_change(12))
        F = pd.DataFrame(feats).dropna(how="all")
        F["namm50_score"] = F.mean(axis=1)
        return F

    def main():
        if not API_KEY:
            raise RuntimeError("FRED_API_KEY not found")
        frames = {}
        for sid in SERIES:
            s = fred_series(sid, observation_start="1990-01-01")
            if s.empty: 
                continue
            frames[sid] = align_daily(s)
        df = pd.DataFrame(frames).dropna(how="all")
        F = compute_namm50(df)
        ensure_dir(OUT_FACTORS); ensure_dir(OUT_SCORE)
        df.to_csv(OUT_FACTORS, index=True)
        F[["namm50_score"]].to_csv(OUT_SCORE, index=True)
        print(f"saved {OUT_FACTORS} and {OUT_SCORE}")

    if __name__ == "__main__":
        main()
