
import os, json, time, math, random, io
from datetime import datetime
import requests
import pandas as pd
import numpy as np

from tools.simple_utils import ensure_dir, write_json, ts_now_iso

AV_API = os.getenv("ALPHAVANTAGE_API_KEY","")
SYMBOL = os.getenv("NAMM50_SYMBOL","SPY")
OUT = "docs/models/namm50.json"
FACTOR_JSON = "docs/factors_namm50.json"
RAW_NAAIM = "data/raw/naaim_exposure.csv"
RAW_FRED = "data/raw/fred_namm50.csv"

random.seed(42)
np.random.seed(42)

def log(*a):
    print("[namm50]", *a, flush=True)

def fetch_alpha_daily(symbol: str, api_key: str, max_retries:int=3) -> pd.DataFrame:
    """
    Free AlphaVantage: TIME_SERIES_DAILY_ADJUSTED (full)
    returns df with Date index and 'close' column
    """
    if not api_key:
        raise RuntimeError("Missing ALPHAVANTAGE_API_KEY")
    url = "https://www.alphavantage.co/query"
    params = {
        "function":"TIME_SERIES_DAILY_ADJUSTED",
        "symbol":symbol,
        "outputsize":"full",
        "apikey":api_key
    }
    for k in range(max_retries):
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            time.sleep(12)
            continue
        data = r.json()
        if any(key for key in data.keys() if "Note" in key or "Thank you" in key):
            # rate limited
            log("Rate limited, sleeping 13s...")
            time.sleep(13)
            continue
        ts = data.get("Time Series (Daily)")
        if not ts:
            log("Unexpected response keys:", list(data.keys())[:3])
            time.sleep(12)
            continue
        rows = []
        for d, v in ts.items():
            try:
                close = float(v.get("5. adjusted close") or v.get("4. close"))
            except Exception:
                continue
            rows.append((pd.to_datetime(d), close))
        if not rows:
            time.sleep(12)
            continue
        df = pd.DataFrame(rows, columns=["date","close"]).sort_values("date").set_index("date")
        return df
    raise RuntimeError("AlphaVantage daily fetch failed repeatedly.")

def try_load_json_series(path:str):
    if not os.path.exists(path):
        return {}
    try:
        obj = json.load(open(path,"r",encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    fac = obj.get("factors",{})
    # expected keys: 'naaim_exposure': {'series': [...]}, 'fred_macro':{'series':[...]} etc.
    for k,v in fac.items():
        ser = v.get("series")
        if ser is None:
            continue
        # Try robust parse: accept [ [date, value], ... ] or [ [*, value, *], ... ]
        rows=[]
        for item in ser:
            if not isinstance(item,(list,tuple)) or len(item)==0:
                continue
            # try pick last numeric as value
            val=None
            for x in reversed(item):
                try:
                    val = float(x)
                    break
                except Exception:
                    continue
            # try find date in first positions
            d=None
            for x in item:
                if isinstance(x,str) and len(x)>=8 and x[0].isdigit():
                    d=x
                    break
            if d is None:
                continue
            try:
                rows.append((pd.to_datetime(d), float(val) if val is not None else np.nan))
            except Exception:
                continue
        if rows:
            df = pd.DataFrame(rows, columns=["date",k]).dropna().drop_duplicates("date").sort_values("date").set_index("date")
            out[k]=df
    return out

def try_load_csvs():
    res={}
    if os.path.exists(RAW_NAAIM):
        df = pd.read_csv(RAW_NAAIM)
        # heuristics: expect columns like date,value or Date, Exposure
        cols = [c.lower() for c in df.columns]
        if "date" in cols:
            date_col = df.columns[cols.index("date")]
        else:
            date_col = df.columns[0]
        val_col = None
        for name in ["value","exposure","exposure_index","naaim","naaime"]:
            if name in cols:
                val_col = df.columns[cols.index(name)]
                break
        if val_col is None:
            # guess second column
            val_col = df.columns[1] if len(df.columns)>1 else df.columns[0]
        try:
            df = df[[date_col,val_col]].rename(columns={date_col:"date", val_col:"naaim_exposure"})
            df["date"]=pd.to_datetime(df["date"])
            df = df.dropna().sort_values("date").set_index("date")
            res["naaim_exposure"]=df[["naaim_exposure"]]
        except Exception:
            pass

    if os.path.exists(RAW_FRED):
        df = pd.read_csv(RAW_FRED)
        # expected cols: DGS10, DFF
        for c in df.columns:
            if c.lower()=="date":
                df["date"]=pd.to_datetime(df["date"])
                df=df.set_index("date")
                break
        # create features with safe conversion
        def to_float(s):
            try:
                return pd.to_numeric(df[s], errors="coerce")
            except Exception:
                return None
        dgs10 = to_float("DGS10")
        dff = to_float("DFF")
        feats = []
        if dgs10 is not None:
            feats.append(("fred_dgs10", dgs10))
        if dff is not None:
            feats.append(("fred_dff", dff))
        if dgs10 is not None and dff is not None:
            feats.append(("curve10y2y", dgs10 - dff))
        parts = []
        for name, series in feats:
            parts.append(series.rename(name).to_frame())
        if parts:
            fred = pd.concat(parts, axis=1)
            res["fred_macro"]=fred
    return res

def build_feature_df() -> pd.DataFrame:
    parts=[]
    # 1) try factors json
    js = try_load_json_series(FACTOR_JSON)
    for k,df in js.items():
        # names might be 'naaim_exposure' or 'fred_macro'
        parts.append(df)
    # 2) fallback csvs
    csvs = try_load_csvs()
    for k,df in csvs.items():
        parts.append(df)
    if not parts:
        raise RuntimeError("No factor data found. Make sure publish-factors workflow ran.")
    feat = pd.concat(parts, axis=1).sort_index()
    # sanitize column names to a friendly set used by donut
    rename = {
        "naaim_exposure":"NAAM",
        "fred_macro":"FRED",
        "fred_dgs10":"DGS10",
        "fred_dff":"DFF",
        "curve10y2y":"CURVE10Y2Y",
    }
    # flatten multi-columns from fred_macro if any
    newcols={}
    for c in feat.columns:
        base = c.split(".")[-1]
        uc = base.upper()
        if uc in ["DGS10","DFF","CURVE10Y2Y","CURVE10Y3M","CPIAUSCL","UNRATE"]:
            newcols[c]=uc
        elif "NAAI" in uc or "EXPOS" in uc:
            newcols[c]="NAAM"
        else:
            newcols[c]=uc
    feat = feat.rename(columns=newcols)
    # drop duplicated columns keeping first
    feat = feat.loc[:, ~feat.columns.duplicated()]
    return feat

def prep_features_prices(symbol: str):
    prices = fetch_alpha_daily(symbol, AV_API)
    prices = prices[prices.index>=pd.Timestamp("2010-01-01")]
    feat = build_feature_df()
    # align by date
    df = prices.join(feat, how="inner")
    # compute returns
    df["ret"] = np.log(df["close"]).diff()
    # z-score features (126d rolling)
    fcols = [c for c in df.columns if c not in ["close","ret"]]
    for c in fcols:
        x = df[c].astype(float)
        roll_mean = x.rolling(126,min_periods=90).mean()
        roll_std = x.rolling(126,min_periods=90).std().replace(0,np.nan)
        z = (x - roll_mean) / roll_std
        df[c] = z.fillna(0.0).clip(-5,5)
    df = df.dropna(subset=["ret"])
    return df, fcols

def evaluate(df: pd.DataFrame, w: np.ndarray, fcols, threshold:float=0.0):
    sig = np.zeros(len(df))
    X = df[fcols].values
    sig = (X @ w)
    pos = (sig > threshold).astype(float)  # long/flat
    # trade next day -> shift
    pnl = pos[:-1] * df["ret"].values[1:]
    if pnl.std()==0:
        sharpe = 0.0
    else:
        sharpe = pnl.mean()/pnl.std()*math.sqrt(252.0)
    ann = pnl.mean()*252.0
    dd = (pd.Series(np.cumsum(pnl)).cummax() - pd.Series(np.cumsum(pnl))).max()
    return sharpe, ann, float(dd), pos[-1], sig[-1]

def random_search(df, fcols, trials:int=200):
    best = (-9e9, None, None, None, None, None)  # sharpe, w, ann, dd, last_pos, last_sig
    k = len(fcols)
    for t in range(trials):
        raw = np.random.rand(k)
        if raw.sum()==0:
            continue
        w = raw / raw.sum()
        thr = np.random.uniform(-0.2,0.2)
        s, ann, dd, last_pos, last_sig = evaluate(df, w, fcols, threshold=thr)
        if s > best[0]:
            best = (s, w, ann, dd, last_pos, last_sig)
    return best

def main():
    log("Training NAMM-50 on", SYMBOL)
    df, fcols = prep_features_prices(SYMBOL)
    log("features:", fcols)
    sharpe, w, ann, dd, last_pos, last_sig = random_search(df, fcols, trials=300)
    if w is None:
        raise RuntimeError("Search failed")
    # pack weights dict into donut families expected by UI
    weights = {
        "NAAM":0.0, "FRED":0.0, "NDX50":0.0, "CHINA":0.0,
        "VIXCLS":0.0, "CURVE10Y2Y":0.0, "CURVE10Y3M":0.0,
        "CPIAUSCL":0.0, "UNRATE":0.0
    }
    # Assign discovered fcols into families
    for name, weight in zip(fcols, w):
        key = name.upper()
        family = None
        if "NAAM" in key:
            family = "NAAM"
        elif key in ["DGS10","DFF","CPIAUSCL","UNRATE","CURVE10Y2Y","CURVE10Y3M","FRED"]:
            # group to FRED unless specific curve column present
            if key in weights:
                family = key
            else:
                family = "FRED"
        elif "NDX" in key:
            family = "NDX50"
        elif "CHINA" in key or "FXI" in key:
            family = "CHINA"
        else:
            # unknown -> fold into FRED bucket
            family = "FRED"
        weights[family] = weights.get(family, 0.0) + float(weight)

    # normalize buckets
    total = sum(weights.values())
    if total>0:
        for k in list(weights.keys()):
            weights[k] = round(weights[k]/total, 4)
    else:
        weights["NAAM"]=1.0

    regime = "Neutral"
    if last_sig>0.5:
        regime = "Risk-On"
    elif last_sig<-0.5:
        regime = "Risk-Off"

    playbook = f"{regime}：观察为主；仅在强信号共振时加/减仓。保持中性敞口。"

    out = {
        "as_of": ts_now_iso(),
        "model":"NAMM-50",
        "version":"v0.2-free",
        "symbol": SYMBOL,
        "horizon":"Daily",
        "weights": weights,
        "metrics": {
            "sharpe": round(float(sharpe),3),
            "ann_return": round(float(ann),3),
            "max_drawdown": round(float(dd),3),
            "trials": 300
        },
        "latest": {
            "signal": round(float(last_sig),3),
            "position": float(last_pos),
            "note": "Auto-trained with free data; only available factors are used.",
            "playbook": playbook
        }
    }
    ensure_dir(OUT)
    write_json(OUT, out)
    log("Wrote", OUT, "keys=", list(out.keys()))

if __name__ == "__main__":
    main()
