
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from tools.utils import ensure_dir, ts_now_iso, zscore, rolling_sharpe

FACTORS_JSON = "docs/factors_namm50.json"
MODEL_OUT = "docs/models/namm50.json"

def load_factors(path=FACTORS_JSON):
    with open(path, "r", encoding="utf-8") as f:
        js = json.load(f)
    facs = js.get("factors", {})
    frames = {}
    for k, v in facs.items():
        ser = v.get("series", [])
        if not ser: 
            continue
        # series is [[ts, value, weight], ...]
        df = pd.DataFrame(ser, columns=["date", "value", "weight"])
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).set_index("date").sort_index()
        frames[k] = df
    return frames

def build_signal(frames: dict) -> pd.DataFrame:
    # align all on common index (inner join of available factors)
    if not frames: 
        return pd.DataFrame(columns=["score"])
    # z-score each factor, then average (equal weight for now)
    zs = []
    for k, df in frames.items():
        s = zscore(df["value"]).rename(k)
        zs.append(s)
    Z = pd.concat(zs, axis=1).dropna(how="all")
    if Z.empty:
        return pd.DataFrame(columns=["score"])
    score = Z.mean(axis=1).to_frame("score")
    return score

def calc_perf(score: pd.DataFrame) -> dict:
    if score is None or score.empty:
        return {"latest_score": None, "sharpe_252": None}
    # naive PnL proxy: day-over-day score change
    pnl = score["score"].diff().fillna(0.0)
    sharpe = float(rolling_sharpe(pnl, win=252).iloc[-1]) if len(pnl) >= 10 else None
    return {"latest_score": float(score["score"].iloc[-1]), "sharpe_252": sharpe}

def main():
    frames = load_factors()
    signal = build_signal(frames)
    perf = calc_perf(signal)

    out = {
        "as_of": ts_now_iso(),
        "model": "NAMM-50",
        "version": "v0.1",
        "weights": {k: 1.0/len(frames) for k in frames} if frames else {},
        "latest": perf,
    }
    ensure_dir(MODEL_OUT)
    with open(MODEL_OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"wrote {MODEL_OUT}, keys={list(out.keys())}")

if __name__ == "__main__":
    main()
