#!/usr/bin/env python3
import os, sys, json, time, math, argparse, textwrap
from datetime import datetime
from typing import Dict, List
import requests
import pandas as pd
import numpy as np
DEFAULT_SYMBOLS=["TQQQ","SOXL"]
def fetch_alpha_daily(symbol, api_key, outputsize="full", max_retries=6, sleep_sec=60):
    url="https://www.alphavantage.co/query"
    sizes=[outputsize]
    # The "full" output size requires a premium key for some endpoints.
    # If the call fails with a premium message, retry with the free
    # "compact" size so the backtest can still run with a basic key.
    if outputsize=="full":
        sizes.append("compact")
    for osize in sizes:
        params={"function":"TIME_SERIES_DAILY_ADJUSTED","symbol":symbol,
                "outputsize":osize,"apikey":api_key}
        for k in range(max_retries):
            r=requests.get(url,params=params,timeout=30);r.raise_for_status();j=r.json()
            if "Time Series (Daily)" in j:
                ts=j["Time Series (Daily)"];df=pd.DataFrame.from_dict(ts,orient="index");df.index=pd.to_datetime(df.index)
                df=df.rename(columns={"1. open":"open","2. high":"high","3. low":"low","4. close":"close","5. adjusted close":"adj_close","6. volume":"volume"})
                cols=["open","high","low","close","adj_close","volume"]
                for c in cols: df[c]=pd.to_numeric(df[c],errors="coerce")
                df=df.sort_index();return df[cols]
            msg=j.get("Note") or j.get("Information") or j.get("Error Message") or "Unknown response"
            # if we receive a premium endpoint message while requesting
            # the full dataset, break and try the smaller compact size
            if "premium" in msg.lower() and osize=="full":
                break
            if k==max_retries-1: raise RuntimeError(f"Alpha Vantage: {msg}")
            time.sleep(sleep_sec)
    raise RuntimeError("Alpha Vantage retry loop exited unexpectedly")
def compute_features(dfd):
    px=dfd["adj_close"].copy();feats=pd.DataFrame(index=dfd.index);r1=px.pct_change();feats["ret_1"]=r1
    feats["ret_5"]=px.pct_change(5);feats["ret_20"]=px.pct_change(20)
    feats["sma_5"]=dfd["adj_close"].rolling(5).mean()/dfd["adj_close"]-1
    feats["sma_20"]=dfd["adj_close"].rolling(20).mean()/dfd["adj_close"]-1
    feats["mom_20"]=dfd["adj_close"].pct_change(20)
    prev=dfd["close"].shift(1);tr=pd.concat([(dfd["high"]-dfd["low"]).abs(),(dfd["high"]-prev).abs(),(dfd["low"]-prev).abs()],axis=1).max(axis=1)
    feats["atr_14"]=tr.rolling(14).mean()/dfd["adj_close"]
    feats["vol_10"]=r1.rolling(10).std()*math.sqrt(252)
    delta=dfd["adj_close"].diff();up=delta.clip(lower=0).rolling(14).mean();down=(-delta.clip(upper=0)).rolling(14).mean();rs=up/(down+1e-9);rsi=100-100/(1+rs)
    feats["rsi_n"]=(rsi-50)/50;feats=feats.replace([np.inf,-np.inf],np.nan).dropna();return feats
def forward_returns(px,h): return px.shift(-h)/px-1.0
def ridge_fit(X,y,l2=1.0):
    XT=X.T;A=XT@X+l2*np.eye(X.shape[1]);b=XT@y
    try: w=np.linalg.solve(A,b)
    except np.linalg.LinAlgError: w=np.linalg.pinv(A)@b
    return w
def walkforward_pred(feats,target,refit_freq="M",lookback=504,l2=1.0):
    idx=feats.index;months=pd.Series(idx,index=idx).resample(refit_freq).first().dropna();preds=pd.Series(index=idx,dtype=float);mu=sig=w=None
    for i,refit_start in enumerate(months.index):
        if i==0: continue
        fit_end=refit_start-pd.Timedelta(days=1);fit_start=max(feats.index[0],fit_end-pd.Timedelta(days=lookback))
        Xf=feats.loc[fit_start:fit_end];yf=target.loc[fit_start:fit_end]
        if len(Xf)<100: continue
        mu=Xf.mean();sig=Xf.std(ddof=0).replace(0,np.nan);Xn=(Xf-mu)/(sig+1e-9);Xn=Xn.replace([np.inf,-np.inf],0.0).fillna(0.0)
        w=ridge_fit(Xn.values,yf.values.astype(float),l2=l2)
        pred_end=months.index[i]+pd.offsets.MonthEnd(0);Xa=((feats.loc[refit_start:pred_end]-mu)/(sig+1e-9)).replace([np.inf,-np.inf],0.0).fillna(0.0)
        if len(Xa)==0: continue
        preds.loc[Xa.index]=Xa.values@w
    return preds.fillna(method="ffill").fillna(0.0)
def build_strategy(px,preds,cost_bps_per_side=0.0005):
    r1=px.pct_change().fillna(0.0);pos=(preds>0).astype(int);chg=pos.diff().abs().fillna(0.0);costs=chg*cost_bps_per_side;ret=pos.shift(1).fillna(0.0)*r1-costs;eq=(1.0+ret).cumprod()
    return {"ret":ret,"pos":pos,"eq":eq}
def stats_from_equity(eq,ret,pos):
    eq=eq.dropna();ret=ret.dropna();n=len(ret)
    if n<10: return {"cagr":0.0,"sharpe":0.0,"maxdd":0.0,"winrate":0.0,"avg_hold":0.0,"turnover":0.0}
    cagr=float(eq.iloc[-1]**(252.0/n)-1.0);vol=float(ret.std(ddof=0));sharpe=float((ret.mean()/(vol+1e-12))*math.sqrt(252.0)) if vol>0 else 0.0
    peak=eq.cummax();maxdd=float((eq/peak-1.0).min());winrate=float((ret>0).mean())
    runs=[];cur=0
    for v in pos.fillna(0).astype(int).values:
        if v==1: cur+=1
        elif cur>0: runs.append(cur);cur=0
    if cur>0: runs.append(cur)
    avg=float(np.mean(runs)) if runs else 0.0;turn=float(pos.diff().abs().sum()/2.0);months=max(1,len(pos)/21.0);turn_pm=float(turn/months)
    return {"cagr":cagr,"sharpe":sharpe,"maxdd":maxdd,"winrate":winrate,"avg_hold":avg,"turnover":turn_pm}
def build_backtests(symbols,api_key,start,version,horizons):
    out={"as_of":datetime.utcnow().isoformat(),"symbols":{}}
    for sym in symbols:
        df=fetch_alpha_daily(sym,api_key,outputsize="full");
        if start: df=df.loc[pd.to_datetime(start):]
        feats=compute_features(df);px=df.loc[feats.index,"adj_close"]
        out["symbols"].setdefault(sym,{});out["symbols"][sym].setdefault(version,{})
        for hz in horizons:
            tgt=px.shift(-hz)/px-1.0;preds=walkforward_pred(feats,tgt,refit_freq="M",lookback=504,l2=1.0)
            strat=build_strategy(px,preds);stats=stats_from_equity(strat["eq"],strat["ret"],strat["pos"]) ;eq=[[int(ts.timestamp()*1000),float(v)] for ts,v in strat["eq"].dropna().items()]
            out["symbols"][sym][version][f"{hz}D"]={"stats":stats,"equity":eq}
    return out
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--symbols",type=str,default="TQQQ,SOXL");p.add_argument("--start",type=str,default="2012-01-01");p.add_argument("--version",type=str,default="v1.6.1");p.add_argument("--out",type=str,default="./docs/backtests.json");p.add_argument("--registry",type=str,default="");p.add_argument("--horizons",type=str,default="3,12,21")
    args=p.parse_args();api_key=os.getenv("ALPHAVANTAGE_API_KEY","" ).strip()
    if not api_key: print("ERROR: Set ALPHAVANTAGE_API_KEY",file=sys.stderr);sys.exit(2)
    symbols=[s.strip().upper() for s in args.symbols.split(",") if s.strip()];horizons=[int(x) for x in args.horizons.split(",")]
    bt=build_backtests(symbols,api_key,args.start,args.version,horizons)
    os.makedirs(os.path.dirname(args.out),exist_ok=True)
    with open(args.out,"w",encoding="utf-8") as f: json.dump(bt,f,ensure_ascii=False)
    if args.registry:
        reg={"universe":[{"symbol":s,"label":f"{s} — AM {args.version}"} for s in symbols],"models":{},"factors":{},"playbooks":{}}
        with open(args.registry,"w",encoding="utf-8") as f: json.dump(reg,f,ensure_ascii=False)
if __name__=="__main__": main()
