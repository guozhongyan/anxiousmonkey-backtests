import os, requests, pandas as pd, json
from core.utils import ensure_dir

API = os.environ.get("FRED_API_KEY")
OUT = "data/raw/fred_bundle.csv"


def get_series():
    try:
        reg = json.load(open("factor_registry.yml", "r", encoding="utf-8"))
        return [v["code"] for v in reg.get("factors", {}).values() if v.get("source") == "fred" and v.get("code")]
    except Exception:
        return []


def fred_series(series_id):
    if not API:
        return None
    url = (
        "https://api.stlouisfed.org/fred/series/observations?series_id="
        f"{series_id}&api_key={API}&file_type=json"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()
    obs = js.get("observations", [])
    df = pd.DataFrame(obs)[["date", "value"]]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.rename(columns={"value": series_id}).set_index("date").sort_index()
    return df


def main():
    series = get_series()
    frames = []
    for s in series:
        try:
            df = fred_series(s)
            if df is not None:
                frames.append(df)
        except Exception as e:
            print(f"FRED fetch failed for {s}: {e}")
    if frames:
        out = pd.concat(frames, axis=1).sort_index()
    else:
        out = pd.DataFrame(columns=["date"] + series)
    ensure_dir(OUT)
    out.to_csv(OUT, index=True, date_format="%Y-%m-%d")
    print(f"saved {OUT}, cols={list(out.columns)}")


if __name__ == "__main__":
    main()
