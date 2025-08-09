\
import os, io, json
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

OUT_CSV = "data/raw/naaim_exposure.csv"
API_KEY = os.environ.get("NASDAQ_API_KEY","").strip()

def try_nasdaq():
    bases = [
        "https://data.nasdaq.com/api/v3/datasets/{code}.json?api_key={key}",
        "https://www.quandl.com/api/v3/datasets/{code}.json?api_key={key}",
    ]
    candidates = [
        "NAAIM/EXPOSURE",
        "NAAIM/NAAIM_EXPOSURE_INDEX",
    ]
    for code in candidates:
        for base in bases:
            url = base.format(code=code, key=API_KEY)
            try:
                r = requests.get(url, timeout=30)
                if r.status_code != 200:
                    continue
                j = r.json()
                if "dataset" in j and "data" in j["dataset"] and "column_names" in j["dataset"]:
                    cols = j["dataset"]["column_names"]
                    data = j["dataset"]["data"]
                    df = pd.DataFrame(data, columns=cols)
                    if "Date" in df.columns: df.rename(columns={"Date":"date"}, inplace=True)
                    if "Value" in df.columns: df.rename(columns={"Value":"value"}, inplace=True)
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"])
                        df = df.sort_values("date")
                        if "value" not in df.columns:
                            for c in df.columns:
                                if c.lower().startswith("exposure") or c.lower().startswith("index"):
                                    df.rename(columns={c:"value"}, inplace=True)
                                    break
                        if "value" in df.columns:
                            return df[["date","value"]].dropna()
            except Exception:
                continue
    return None

def fallback_scrape_excel():
    # Find downloadable excel on NAAIM page
    url = "https://naaim.org/programs/naaim-exposure-index/"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    link = None
    for a in soup.find_all("a"):
        href = a.get("href","")
        if href and ("xlsx" in href or "xls" in href):
            link = href
            break
    if not link:
        return None
    er = requests.get(link, timeout=120)
    if er.status_code != 200:
        return None
    try:
        df = pd.read_excel(io.BytesIO(er.content))
    except Exception:
        return None
    # Heuristic columns
    cand = [c for c in df.columns if str(c).strip().lower().startswith("date")]
    vcand = [c for c in df.columns if "mean" in str(c).lower() or "average" in str(c).lower() or "number" in str(c).lower() or "exposure" in str(c).lower()]
    if not cand or not vcand:
        return None
    df = df.rename(columns={cand[0]:"date", vcand[0]:"value"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").dropna(subset=["value"])
    return df[["date","value"]]

def main():
    df = None
    if API_KEY:
        df = try_nasdaq()
    if df is None:
        df = fallback_scrape_excel()
    # if still None, write empty csv to avoid failing the workflow (no fake data)
    if df is None or df.empty:
        os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
        pd.DataFrame(columns=["date","value"]).to_csv(OUT_CSV, index=False)
        print("NAAIM: no data fetched this run; wrote empty CSV.")
        return
    df = df.dropna().copy()
    df = df[df["value"].apply(lambda x: np.isfinite(x))]
    df = df.drop_duplicates(subset=["date"]).sort_values("date")
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"saved {OUT_CSV}, rows={len(df)}")

if __name__ == "__main__":
    main()
