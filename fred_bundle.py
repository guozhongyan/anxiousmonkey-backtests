import os, sys, pandas as pd, requests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.utils import safe_write_csv, write_placeholder_csv

OUT_CSV = "data/raw/fred_namm50.csv"
API_KEY = os.environ.get("FRED_API_KEY","").strip()

def fred_api(series_id: str):
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={API_KEY}&file_type=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()
    arr = js.get("observations",[])
    df = pd.DataFrame([{"date":a["date"], "value": float(a["value"]) if a["value"] not in (".","") else None} for a in arr])
    df = df.dropna()
    return df

def fred_csv(series_id: str):
    # 公共 CSV 兜底（无 KEY）
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    import io
    df = pd.read_csv(io.StringIO(r.text))
    # 标准化
    df = df.rename(columns={series_id:"value"})
    df = df[["DATE","value"]].rename(columns={"DATE":"date"}).dropna()
    return df

def main():
    try:
        if API_KEY:
            dgs10 = fred_api("DGS10")
            dff   = fred_api("DFF")
        else:
            dgs10 = fred_csv("DGS10")
            dff   = fred_csv("DFF")
        # 合并并对齐
        m = pd.merge(dgs10, dff, on="date", how="inner", suffixes=("_DGS10","_DFF"))
        safe_write_csv(m, OUT_CSV)
        print(f"saved {OUT_CSV}, cols={['DGS10','DFF']}, rows={len(m)}")
        return
    except Exception as e:
        print("[warn] fred bundle failed:", e)
    # 最终兜底：占位（列名与历史保持）
    write_placeholder_csv(OUT_CSV, ["date","DGS10","DFF"])
    print(f"[placeholder] wrote empty {OUT_CSV}")

if __name__ == "__main__":
    main()
