
import os, json
import pandas as pd
import numpy as np
from core.utils import ensure_dir, ts_now_iso, write_json

PRICES_JSON = "docs/prices.json"
OUT_JSON = "docs/backtests.json"

def sharpe(series):
    if len(series) < 2: return 0.0
    rets = pd.Series(series).pct_change().dropna()
    if rets.std(ddof=0) == 0 or rets.empty: return 0.0
    return float(rets.mean() / rets.std(ddof=0))

def main():
    if not os.path.exists(PRICES_JSON):
        write_json(OUT_JSON, {"as_of": ts_now_iso(), "error": "no prices.json"})
        return
    with open(PRICES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    prices = data.get("prices", {})
    sharpe_map = {}
    for sym, rows in prices.items():
        closes = [v for _, v in rows]
        sharpe_map[sym] = round(sharpe(closes), 4)
    out = {"as_of": ts_now_iso(), "model": "Backtest from docs/prices.json", "sharpe": sharpe_map}
    write_json(OUT_JSON, out)

if __name__ == "__main__":
    main()
