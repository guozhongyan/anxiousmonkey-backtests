import pandas as pd, yfinance as yf
from core.utils import ensure_dir

OUT = "data/raw/china_proxy_fxi.csv"


def main():
    try:
        df = yf.download("FXI", period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
    except Exception as e:
        print(f"FXI download failed: {e}")
        df = pd.DataFrame()
    if df is None or df.empty:
        print("FXI empty; writing placeholder")
        ensure_dir(OUT)
        pd.DataFrame({"date": [], "close": [], "z": []}).to_csv(OUT, index=False)
        return
    df = df[["Close"]].rename(columns={"Close": "close"})
    s = df["close"].pct_change().rolling(5).mean() * 100.0
    z = (s - s.rolling(60).mean()) / s.rolling(60).std(ddof=0)
    df["z"] = z
    ensure_dir(OUT)
    df.to_csv(OUT, index=True, date_format="%Y-%m-%d")
    print(f"saved {OUT}, rows={len(df)}")


if __name__ == "__main__":
    main()
