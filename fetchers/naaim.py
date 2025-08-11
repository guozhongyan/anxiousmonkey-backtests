import os
import io
import requests
import pandas as pd

from core.utils import ensure_dir


OUT = "data/raw/naaim_exposure.csv"
URLS = [
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
]


def fetch(url: str) -> str:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def parse(text: str) -> pd.DataFrame | None:
    df = pd.read_csv(io.StringIO(text))
    cols = [c.lower() for c in df.columns]
    df.columns = cols
    if "value" not in df and "exposure" in df:
        df["value"] = df["exposure"]
    if "date" in df and "value" in df:
        df = df[["date", "value"]]
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")
        return df
    return None


def main() -> None:
    df = None
    for url in URLS:
        try:
            txt = fetch(url)
            df = parse(txt)
            if df is not None:
                break
        except Exception as e:  # noqa: BLE001
            print(f"fetch failed {url}: {e}")

    if df is not None and not df.empty:
        ensure_dir(OUT)
        df.to_csv(OUT, index=False)
        print(f"saved {OUT}, rows={len(df)}")
        return

    if os.path.exists(OUT):
        print("fallback: keep existing file")
        return

    ensure_dir(OUT)
    pd.DataFrame([{"date": pd.Timestamp.today().normalize(), "value": None}]).to_csv(
        OUT, index=False
    )
    print("wrote placeholder NAAIM file")


if __name__ == "__main__":
    main()

