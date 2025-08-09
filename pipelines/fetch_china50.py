\
    import os, json
    import pandas as pd
    import yfinance as yf
    from tools.utils import ensure_dir

    OUT_CSV = "data/raw/china50.csv"
    TICKERS = ["FXI", "XIN9.L"]  # ETF proxy + London listing

    def main():
        frames = []
        for t in TICKERS:
            try:
                df = yf.download(t, period="10y", interval="1d", auto_adjust=False, progress=False, threads=False)
                if df is None or df.empty:
                    continue
                s = df["Adj Close"].rename(t)
                frames.append(s)
            except Exception:
                continue
        if not frames:
            raise RuntimeError("No China50 data from Yahoo")
        out = pd.concat(frames, axis=1).sort_index()
        ensure_dir(OUT_CSV)
        out.to_csv(OUT_CSV, index=True)
        print(f"saved {OUT_CSV}, cols={list(out.columns)}")

    if __name__ == "__main__":
        main()
