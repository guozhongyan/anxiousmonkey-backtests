\
    import os, json
    import pandas as pd
    from tools.utils import ts_now_iso, label_from_score, to_json_ready, ensure_dir

    FACTORS_CSV = "data/raw/namm50_components.csv"
    SCORE_CSV = "data/raw/namm50_score.csv"
    NAAIM_CSV = "data/raw/naaim_exposure.csv"
    NDX_BREADTH_CSV = "data/raw/ndx_breadth_50dma.csv"
    CHINA50_CSV = "data/raw/china50.csv"

    OUT_FACTORS_JSON = "docs/factors_namm50.json"
    OUT_BACKTESTS_JSON = "docs/backtests.json"

    def load_csv(path, date_col=None):
        if not os.path.exists(path):
            return None
        if date_col is None:
            return pd.read_csv(path, parse_dates=[0])
        return pd.read_csv(path, parse_dates=[date_col])

    def main():
        as_of = ts_now_iso()
        F = load_csv(FACTORS_CSV); S = load_csv(SCORE_CSV)
        if F is None or S is None:
            raise RuntimeError("Missing NAMM-50 inputs")
        F = F.set_index(F.columns[0]); S = S.set_index(S.columns[0])
        naaim = load_csv(NAAIM_CSV)
        ndx = load_csv(NDX_BREADTH_CSV)
        cn = load_csv(CHINA50_CSV)

        last_score = float(S.iloc[-1,0])
        label = label_from_score(last_score)

        data = {
            "as_of": as_of,
            "namm50": {
                "last_score": last_score,
                "label": label,
                "score_series": to_json_ready(S, [S.columns[0]]),
                "components_head": list(F.columns)
            }
        }
        if naaim is not None:
            naaim = naaim.set_index(naaim.columns[0])
            data["namm50"]["naaim_exposure"] = to_json_ready(naaim, [naaim.columns[0]])
        if ndx is not None:
            ndx = ndx.set_index(ndx.columns[0])
            data["namm50"]["ndx_pct_above_50dma"] = to_json_ready(ndx, [ndx.columns[1] if len(ndx.columns)>1 else ndx.columns[0]])
        if cn is not None:
            cn = cn.set_index(cn.columns[0])
            keep = [c for c in cn.columns][:2]
            data["namm50"]["china50"] = to_json_ready(cn, keep)

        ensure_dir(OUT_FACTORS_JSON)
        with open(OUT_FACTORS_JSON, "w") as f:
            json.dump(data, f, separators=(",", ":"))

        back = {"as_of": as_of, "symbols": {}}
        if os.path.exists(OUT_BACKTESTS_JSON):
            try:
                with open(OUT_BACKTESTS_JSON,"r") as f:
                    back0 = json.load(f)
                if isinstance(back0, dict):
                    back = back0
            except Exception:
                pass
        back["as_of"] = as_of
        back.setdefault("overlays", {})
        back["overlays"]["namm50"] = {"label": label, "score": last_score}
        ensure_dir(OUT_BACKTESTS_JSON)
        with open(OUT_BACKTESTS_JSON, "w") as f:
            json.dump(back, f, separators=(",", ":"))
        print(f"Wrote {OUT_FACTORS_JSON} and updated {OUT_BACKTESTS_JSON}")

    if __name__ == "__main__":
        main()
