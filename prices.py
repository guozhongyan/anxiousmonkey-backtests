
import os, json, time, requests
from core.utils import ensure_dir, ts_now_iso, write_json

API_KEY = os.environ.get('ALPHAVANTAGE_API_KEY', '')
SYMBOLS = os.environ.get('AM_SYMBOLS', 'SOXL,QQQ,SPY,NVDA').split(',')

def fetch_daily_close(sym):
    # Use free endpoint TIME_SERIES_DAILY (compact)
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={sym}&outputsize=compact&apikey={API_KEY}'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()
    ts = js.get('Time Series (Daily)') or {}
    if not ts:
        raise RuntimeError(f'Alpha Vantage returned no data for {sym}: {js.get("Note") or js.get("Error Message") or "unknown"}')
    # latest date
    d = sorted(ts.keys())[-1]
    c = float(ts[d]['4. close'])
    return {"symbol": sym, "date": d, "close": c}

def main():
    ensure_dir('docs')
    out = {"as_of": ts_now_iso(), "prices": []}
    for i, s in enumerate(SYMBOLS):
        s = s.strip()
        if not s:
            continue
        try:
            out["prices"].append(fetch_daily_close(s))
            # Basic rate limit protection (5 req/min for free keys)
            if i % 4 == 4:
                time.sleep(60)
        except Exception as e:
            out["prices"].append({"symbol": s, "error": str(e)})
    write_json('docs/prices.json', out, indent=2)
    print('wrote docs/prices.json with', len(out["prices"]), 'items')

if __name__ == '__main__':
    main()
