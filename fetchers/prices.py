
import os, json, time, requests, sys, datetime as dt

API = os.environ.get("ALPHAVANTAGE_API_KEY")
OUT = os.path.join("docs","prices.json")
SYMS = ["TQQQ","QQQ","SPY"]

def fetch_daily(sym):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={sym}&outputsize=compact&apikey={API}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    j = r.json()
    ts = j.get("Time Series (Daily)", {})
    rows = []
    for k,v in sorted(ts.items()):
        rows.append([k, float(v["4. close"])])
    return rows[-200:]

def main():
    if not API:
        print("ALPHAVANTAGE_API_KEY missing"); sys.exit(0)
    out = {"as_of": dt.datetime.utcnow().isoformat(timespec="seconds")+"Z", "tickers":[]}
    for i,s in enumerate(SYMS):
        try:
            data = fetch_daily(s)
            last = data[-1][1] if data else None
            prev = data[-2][1] if len(data)>1 else last
            chg = None if (last is None or prev is None or prev==0) else (last/prev - 1.0)
            out["tickers"].append({"symbol":s, "price":last, "change":chg})
            time.sleep(12)  # respect rate limit
        except Exception as e:
            out["tickers"].append({"symbol":s, "price":None, "change":None, "error":str(e)[:120]})
            time.sleep(12)
    os.makedirs("docs", exist_ok=True)
    with open(OUT,"w") as f: json.dump(out, f)
    print("wrote", OUT)

if __name__=="__main__":
    main()
