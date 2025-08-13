# -*- coding: utf-8 -*-
"""
Fetch spot prices via Alpha Vantage GLOBAL_QUOTE (free; ~15min delayed).
Falls back to TIME_SERIES_DAILY (EOD) if GLOBAL_QUOTE fails.
Output: docs/prices.json
"""
import os, json, time, requests, datetime as dt
from pathlib import Path

API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "")
if not API_KEY:
    raise SystemExit("ALPHAVANTAGE_API_KEY is not set in Actions secrets.")

OUT = Path("docs/prices.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Add/adjust your symbols here
SYMBOLS = ["SPY", "QQQ", "TQQQ", "SOXL", "FEZ", "CURE"]

BASE = "https://www.alphavantage.co/query"

def av_get(params: dict):
    params = {**params, "apikey": API_KEY}
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    # Alpha Vantage sometimes returns note/rate limit info with 200
    if any(k in data for k in ("Note", "Information")):
        raise RuntimeError(data.get("Note") or data.get("Information"))
    return data

def fetch_global_quote(symbol: str) -> float:
    data = av_get({"function": "GLOBAL_QUOTE", "symbol": symbol})
    q = data.get("Global Quote") or {}
    px = q.get("05. price")
    if px is None:
        raise RuntimeError(f"GLOBAL_QUOTE missing for {symbol}")
    return float(px)

def fetch_daily_close(symbol: str) -> float:
    data = av_get({"function": "TIME_SERIES_DAILY", "symbol": symbol})
    ts = data.get("Time Series (Daily)") or {}
    if not ts:
        raise RuntimeError(f"TIME_SERIES_DAILY missing for {symbol}")
    last_day = sorted(ts.keys())[-1]
    px = ts[last_day]["4. close"]
    return float(px)

def read_previous():
    try:
        return json.loads(OUT.read_text())
    except Exception:
        return {"symbols": []}

def main():
    prev = read_previous()
    out = {
        "as_of": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "symbols": []
    }

    for idx, sym in enumerate(SYMBOLS):
        # Free plan: 5 req/min; be conservative
        if idx:
            time.sleep(13)
        px = None
        err = None
        try:
            px = fetch_global_quote(sym)
        except Exception as e:
            err = str(e)
            try:
                # fallback to EOD
                px = fetch_daily_close(sym)
                err = None
            except Exception as e2:
                err = f"{err} | fallback: {e2}"

        if px is not None:
            out["symbols"].append({"symbol": sym, "price": round(px, 2)})
        else:
            # keep previous value if exists, but annotate error
            prev_map = {x.get("symbol"): x for x in prev.get("symbols", [])}
            prev_entry = prev_map.get(sym)
            if prev_entry and "price" in prev_entry:
                out["symbols"].append({"symbol": sym, "price": prev_entry["price"], "warning": err})
            else:
                out["symbols"].append({"symbol": sym, "error": err or "unknown error"})

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
