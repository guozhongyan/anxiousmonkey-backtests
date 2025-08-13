
import csv, io, requests
from core.utils import ensure_dir, ts_now_iso

OUT = "data/raw/naaim_exposure.csv"
URLS = [
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim-exposure-index.csv"
]

def fetch(url: str) -> str:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def parse(text: str):
    df = []
    reader = csv.DictReader(io.StringIO(text))
    cols = [c.lower() for c in reader.fieldnames or []]
    # Normalize headers
    date_key = "date"
    value_key = "value" if "value" in cols else ("exposure" if "exposure" in cols else None)
    for row in reader:
        d = row.get("date") or row.get("Date")
        v = row.get("value") or row.get("Value") or row.get("exposure") or row.get("Exposure")
        if d is not None:
            df.append({"date": d, "value": v})
    return df

def write_csv(rows):
    ensure_dir("data/raw")
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["date","value"])
        wr.writeheader()
        for r in rows:
            wr.writerow(r)

def main():
    last_err = None
    for url in URLS:
        try:
            txt = fetch(url)
            rows = parse(txt)
            if rows:
                write_csv(rows)
                print(f"saved {OUT}, rows={len(rows)}")
                return
        except Exception as e:
            last_err = e
            print(f"fetch failed {url}: {e}")
    # fallback: write empty with header
    write_csv([])
    print("NAAIM fallback: wrote empty csv.")

if __name__ == "__main__":
    main()
