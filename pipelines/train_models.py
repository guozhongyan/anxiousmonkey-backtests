
import os, sys, json, time, math, requests
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import ensure_dir, zscore, ts_now_iso

FACTORS_JSON = "docs/factors_namm50.json"
MODEL_JSON = "docs/models/namm50.json"

ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "")

def fetch_av_daily(symbol, outputsize="compact"):
    if not ALPHAVANTAGE_API_KEY:
        raise RuntimeError("ALPHAVANTAGE_API_KEY missing")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": ALPHAVANTAGE_API_KEY
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    ts = j.get("Time Series (Daily)", {})
    rows = []
    for k, v in ts.items():
        try:
            rows.append([k, float(v["5. adjusted close"])])
        except Exception:
            pass
    if not rows:
        raise RuntimeError("No AV data for " + symbol)
    df = pd.DataFrame(rows, columns=["date","close"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    return df

def load_factors():
    with open(FACTORS_JSON, "r") as f:
        j = json.load(f)
    fac = j.get("factors", {})
    def series_to_df(series, name):
        if not series:
            return None
        rows = []
        for it in series:
            if not it: continue
            d = it[0]; vals = it[1:]
            if not vals: continue
            rows.append([d, vals])
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["date","vals"])
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")
        mx = max(len(v) for v in df["vals"])
        cols = [f"{name}{i+1}" for i in range(mx)]
        data = pd.DataFrame(df["vals"].tolist(), index=df.index, columns=cols)
        return data
    out = {}
    if fac.get("naaim_exposure",{}).get("series"):
        s = series_to_df(fac["naaim_exposure"]["series"], "naaim")
        if s is not None: out["naaim"] = s.iloc[:,0]
    if fac.get("ndx_breadth",{}).get("series"):
        s = series_to_df(fac["ndx_breadth"]["series"], "ndx")
        if s is not None: out["ndx"] = s.iloc[:,0]
    if fac.get("fred_macro",{}).get("series"):
        s = series_to_df(fac["fred_macro"]["series"], "fred")
        if s is not None and s.shape[1] >= 2:
            out["dgs10"] = s.iloc[:,0]; out["dff"] = s.iloc[:,1]
    if fac.get("china_proxy",{}).get("series"):
        s = series_to_df(fac["china_proxy"]["series"], "china")
        if s is not None: out["china"] = s.iloc[:,0]
    if fac.get("vix",{}).get("series"):
        s = series_to_df(fac["vix"]["series"], "vix")
        if s is not None: out["vix"] = s.iloc[:,0]
    df = pd.DataFrame(out).sort_index()
    return df

def compute_signal(df, weights):
    x = pd.DataFrame(index=df.index)
    if "naaim" in df: x["naaim"] = zscore(df["naaim"].astype(float)/100.0)
    if "ndx" in df: x["ndx"] = zscore(df["ndx"].astype(float)/100.0)
    if "dgs10" in df and "dff" in df:
        slope = (df["dgs10"].astype(float) - df["dff"].astype(float))
        x["fred"] = zscore(-slope)
    if "china" in df: x["china"] = zscore(pd.Series(df["china"].astype(float)).pct_change().fillna(0.0))
    if "vix" in df: x["vix"] = zscore(-df["vix"].astype(float))
    for col in ["naaim","ndx","fred","china","vix"]:
        if col not in x: x[col] = 0.0
    w = {
        "NAAM": float(weights.get("NAAM", 0.0)),
        "NDX50": float(weights.get("NDX50", 0.0)),
        "FRED": float(weights.get("FRED", 0.0)),
        "CHINA": float(weights.get("CHINA", 0.0)),
        "VIX": float(weights.get("VIX", 0.0)),
    }
    ws = pd.Series(w)
    if ws.sum() == 0:
        ws = pd.Series({"NAAM":0.4,"FRED":0.3,"NDX50":0.2,"CHINA":0.1,"VIX":0.0})
    comp = (ws["NAAM"]*x["naaim"] + ws["FRED"]*x["fred"] + ws["NDX50"]*x["ndx"] + ws["CHINA"]*x["china"] + ws["VIX"]*x["vix"])
    sig = np.tanh(comp)
    return sig

def sharpe_annualized(rets):
    r = pd.Series(rets).dropna()
    if len(r) < 5: return None
    mu = r.mean(); sd = r.std(ddof=0)
    if sd == 0 or pd.isna(sd): return None
    return float((mu / sd) * (252 ** 0.5))

def max_drawdown(equity):
    x = pd.Series(equity).dropna()
    if x.empty: return None
    roll_max = x.cummax(); dd = x/roll_max - 1.0
    return float(dd.min())

def main():
    base = {
        "as_of": ts_now_iso(),
        "model": "NAMM-50",
        "version": "v2-metrics",
        "weights": {"NAAM":0.4,"FRED":0.3,"NDX50":0.2,"CHINA":0.1,"VIX":0.0}
    }
    if os.path.exists(MODEL_JSON):
        try:
            with open(MODEL_JSON,"r") as f: cur = json.load(f)
            base.update({k:v for k,v in cur.items() if k != "weights"})
            if "weights" in cur and isinstance(cur["weights"], dict):
                base["weights"].update(cur["weights"])
        except Exception: pass

    df = load_factors()

    try:
        px = fetch_av_daily("QQQ", outputsize="compact")
    except Exception as e:
        try:
            time.sleep(12); px = fetch_av_daily("SPY", outputsize="compact")
        except Exception as e2:
            ensure_dir(MODEL_JSON); 
            with open(MODEL_JSON,"w") as f: json.dump(base, f)
            print("No price series; wrote base model only."); 
            return

    rets = px["close"].pct_change().rename("ret")
    df_all = df.join(rets, how="inner")
    if df_all.empty:
        ensure_dir(MODEL_JSON); 
        with open(MODEL_JSON,"w") as f: json.dump(base, f)
        print("No overlap; wrote base model only."); 
        return

    sig = compute_signal(df_all, base["weights"])
    strat_ret = sig.shift(1).fillna(0.0) * df_all["ret"]
    equity = (1.0 + strat_ret).cumprod()

    s_all = sharpe_annualized(strat_ret)
    s_3m = sharpe_annualized(strat_ret.tail(63))
    s_12m = sharpe_annualized(strat_ret.tail(252))
    win_12m = float((strat_ret.tail(252) > 0).mean()) if len(strat_ret) >= 10 else None
    mdd = max_drawdown(equity)

    metrics = {
        "sharpe_all": s_all,
        "sharpe_3m": s_3m,
        "sharpe_12m": s_12m,
        "winrate_12m": win_12m,
        "max_drawdown": mdd
    }
    eq_list = [[d.strftime("%Y-%m-%d"), float(v)] for d,v in equity.dropna().items()]

    out = base.copy(); out["as_of"] = ts_now_iso()
    out["metrics"] = metrics; out["equity_curve"] = eq_list

    ensure_dir(MODEL_JSON)
    with open(MODEL_JSON,"w") as f: json.dump(out, f)
    print("wrote", MODEL_JSON, "rows:", len(eq_list))

if __name__ == "__main__":
    main()
