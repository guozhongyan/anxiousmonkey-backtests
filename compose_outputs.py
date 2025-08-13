
import os, json, csv, datetime
from core.utils import ensure_dir, ts_now_iso, write_json

RAW_NAAIM = 'data/raw/naaim_exposure.csv'
RAW_FRED  = 'data/raw/fred_namm50.csv'   # optional

def read_csv_series(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, 'r', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        for r in rd:
            # expect columns date,value
            d = r.get('date') or r.get('Date') or r.get('DATE')
            v = r.get('value') or r.get('Value') or r.get('VALUE')
            try:
                v = float(v) if v not in (None, '') else None
            except Exception:
                v = None
            if d:
                out.append([d, v])
    return out

def main():
    ensure_dir('docs')
    data = {
        "as_of": ts_now_iso(),
        "factors": {
            "naaim_exposure": {"series": read_csv_series(RAW_NAAIM)},
            "fred_macro": {"series": read_csv_series(RAW_FRED)},
            "ndx_breadth": {"series": None},
            "china_proxy": {"series": None}
        }
    }
    write_json('docs/factors_namm50.json', data, indent=2)
    print('wrote docs/factors_namm50.json with keys:', list(data["factors"].keys()))

if __name__ == '__main__':
    main()
