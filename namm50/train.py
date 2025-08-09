
import os, json, pandas as pd, numpy as np
from tools.utils import ensure_dir, rolling_sharpe, ts_now_iso
from signals.namm50 import combine, regime_from

DATA = {
    "naaim": "data/raw/naaim_exposure.csv",
    "breadth": "data/raw/ndx_breadth_topn.csv",
    "china": "data/raw/china_fxi.csv",
    "fred": "data/raw/fred_bundle.csv"
}

OUT_DIR = "data/models/namm50"
DOC_MODEL = "docs/models/namm50.json"
DOC_BACK = "docs/backtests.json"

def load_series():
    naaim = None
    if os.path.exists(DATA["naaim"]):
        d = pd.read_csv(DATA["naaim"], parse_dates=["date"])
        d = d.rename(columns={d.columns[1]:"value"}).set_index("date").sort_index()
        naaim = d["value"]
    breadth = None
    if os.path.exists(DATA["breadth"]):
        d = pd.read_csv(DATA["breadth"], parse_dates=["date"]).set_index("date").sort_index()
        breadth = d.iloc[:,0]
    china = None
    if os.path.exists(DATA["china"]):
        d = pd.read_csv(DATA["china"], parse_dates=["date"]).set_index("date").sort_index()
        china = d["close"]
    fred = None
    if os.path.exists(DATA["fred"]):
        d = pd.read_csv(DATA["fred"], parse_dates=["date"]).set_index("date").sort_index()
        fred = d.get("10Y", None)
    return naaim, breadth, china, fred

def simulate_equity(regime: pd.Series):
    retw = regime.copy().astype(float)
    retw[regime=="Risk-On"] = 1.0
    retw[regime=="Neutral"] = 0.2
    retw[regime=="Risk-Off"] = -0.5
    market = pd.Series(0.0005, index=regime.index)
    daily = (retw.shift(1).fillna(0) * market)
    equity = (1.0 + daily).cumprod()
    return equity, daily

def main():
    naaim, breadth, china, fred = load_series()
    score = combine(naaim, breadth, china, fred)
    reg = regime_from(score)
    equity, daily = simulate_equity(reg.reindex(score.index).fillna("Neutral"))
    roll63 = rolling_sharpe(daily, 63)
    metrics = {
        "ann_return": float((equity.iloc[-1])**(252/len(daily)) - 1) if len(daily)>10 else None,
        "ann_vol": float(np.std(daily)*np.sqrt(252)) if len(daily)>10 else None,
        "max_dd": float((equity/ equity.cummax() -1).min()) if len(equity)>10 else None
    }
    ensure_dir(OUT_DIR + "/x")
    equity.rename("equity").to_csv(OUT_DIR + "/equity_curve.csv", header=True)
    roll63.rename("rolling_sharpe_63d").to_csv(OUT_DIR + "/rolling_sharpe_63d.csv", header=True)

    model_doc = {
        "as_of": ts_now_iso(),
        "version": "v1.44",
        "regime": str(reg.iloc[-1]) if len(reg)>0 else "Neutral",
        "signal": {"beta_target": 1.0},
        "weights": [["NAAIM", 0.4], ["NDX>50DMA", 0.4], ["China (FXI)", 0.1], ["Macro(FRED)", 0.1]],
        "thresholds": {"naaim_on":60, "breadth_on":50, "risk_off_breadth":30},
        "factors": {
            "naaim_exposure": {"latest": float(naaim.iloc[-1]) if naaim is not None and len(naaim)>0 else None},
            "ndx_breadth": {"latest": float(breadth.iloc[-1]) if breadth is not None and len(breadth)>0 else None},
            "china_proxy": {"latest": float(china.iloc[-1]) if china is not None and len(china)>0 else None}
        }
    }
    ensure_dir(DOC_MODEL)
    with open(DOC_MODEL,"w") as f: json.dump(model_doc, f, indent=2)

    back = {
        "models": {
            "namm50": {
                "version": "v1.44",
                "equity_curve": [[str(d.date()), float(v)] for d,v in equity.dropna().items()],
                "rolling_sharpe_63d": [[str(d.date()), float(v)] for d,v in roll63.dropna().items()],
                "metrics": metrics
            }
        }
    }
    ensure_dir(DOC_BACK)
    with open(DOC_BACK,"w") as f: json.dump(back, f, indent=2)
    print("Wrote", DOC_MODEL, DOC_BACK)

if __name__ == "__main__":
    main()
