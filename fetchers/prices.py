import pandas as pd, yfinance as yf
from core.utils import ensure_dir, write_json, to_json_ready

TICKERS = ["SPY","QQQ","TQQQ","FXI"]
OUT = "docs/prices.json"

def main():
    hist = {}
    for t in TICKERS:
        try:
            df = yf.download(t, period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
            if df is not None and not df.empty:
                hist[t] = df["Close"].rename(t)
        except Exception:
            pass
    if not hist:
        write_json(OUT, {"as_of": None, "series": {}}); return
    px = pd.DataFrame(hist).sort_index()
    ensure_dir(OUT)
    payload = {"as_of": pd.Timestamp.utcnow().isoformat(timespec="seconds")+"Z",
               "series": {k: to_json_ready(px[[k]]) for k in px.columns}}
    write_json(OUT, payload)
    print(f"wrote {OUT}, tickers={list(px.columns)}")
if __name__ == "__main__":
    main()
