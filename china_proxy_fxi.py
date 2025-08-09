
import os, requests, pandas as pd
from tools.utils import ensure_dir

ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY") or os.environ.get("ALPHAVANTAGE")
OUT = "data/raw/china_fxi.csv"

def main():
    if not ALPHAVANTAGE_API_KEY:
        raise SystemExit("Set ALPHAVANTAGE_API_KEY.")
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=FXI&outputsize=compact&apikey={ALPHAVANTAGE_API_KEY}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    j = r.json()
    ts = j.get("Time Series (Daily)", {})
    rows = []
    for d,o in ts.items():
        try:
            rows.append((pd.Timestamp(d), float(o["5. adjusted close"])))
        except Exception:
            continue
    rows.sort()
    df = pd.DataFrame(rows, columns=["date","close"]).set_index("date")
    ensure_dir(OUT)
    df.to_csv(OUT)
    print(f"saved {OUT}, rows={len(df)}")

if __name__ == "__main__":
    main()
