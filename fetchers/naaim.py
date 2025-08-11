# fetchers/naaim.py
import os, io, sys, time
import requests
import pandas as pd

# 兼容项目内模块引用（core.utils）
# 如果你 repo 里是 tools/utils.py，请把下一行改回: from tools.utils import ensure_dir
from core.utils import ensure_dir

# 输出 CSV 路径（保留旧变量名以兼容早期脚本 / 测试）
OUT = "data/raw/naaim_exposure.csv"
OUT_CSV = OUT

# 官方与镜像/备用地址（按顺序尝试）
DEFAULT_URLS = [
    # 官方（有时 404）
    "https://naaim.org/wp-content/uploads/naaim_exposure_index.csv",
    "https://www.naaim.org/wp-content/uploads/naaim_exposure_index.csv",
]

# 可在 CI 或本地通过环境变量追加镜像地址（逗号分隔）
ENV_MIRRORS = os.getenv("NAAIM_MIRROR_URLS", "")
if ENV_MIRRORS.strip():
    DEFAULT_URLS += [u.strip() for u in ENV_MIRRORS.split(",") if u.strip()]


def fetch(url: str, timeout: int = 30) -> str | None:
    """拉取文本，失败返回 None（不抛异常，方便兜底逻辑）"""
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        pass
    return None


def get_text_with_fallbacks(urls, timeout=30):
    """Try each URL until one returns text or all fail."""
    for u in urls:
        txt = fetch(u, timeout=timeout)
        if txt:
            return txt
    return None


def load_prev_csv(path: str) -> pd.DataFrame | None:
    """Load previous CSV if present, else return None."""
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return None
    return None


def parse_csv_text(text: str) -> pd.DataFrame | None:
    """尽量鲁棒地解析 CSV，抽取 date / value 两列"""
    try:
        df = pd.read_csv(io.StringIO(text))
    except Exception:
        return None

    # 统一列名为小写
    df.columns = [str(c).strip().lower() for c in df.columns]

    # 识别数值列：优先 value / exposure / index_exposure
    value_col = None
    for c in ("value", "exposure", "index_exposure", "naaim_exposure", "naaim"):
        if c in df.columns:
            value_col = c
            break
    if value_col is None:
        # 有些表头是两列：date, value，但 value 列名可能是数字/空白，尽量兜底
        numeric_candidates = [c for c in df.columns if c not in ("date",) and df[c].dtype != "O"]
        if numeric_candidates:
            value_col = numeric_candidates[0]
        else:
            return None

    # 识别日期列：date / day / datetime / period …
    date_col = None
    for c in ("date", "day", "datetime", "period"):
        if c in df.columns:
            date_col = c
            break
    if date_col is None:
        # 兜底：如果第一列看起来像日期就用第一列
        first = df.columns[0]
        date_col = first

    # 选择两列并清洗
    try:
        out = df[[date_col, value_col]].rename(columns={date_col: "date", value_col: "value"})
    except Exception:
        return None

    # 转日期 / 数值
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")

    # 清洗并排序
    out = out.dropna(subset=["date", "value"]).drop_duplicates(subset=["date"]).sort_values("date")
    if out.empty:
        return None

    return out[["date", "value"]]


def write_placeholder_when_needed():
    """当抓取失败且不存在旧文件时，写一个空壳 CSV，避免后续流水线中断。"""
    if not os.path.exists(OUT_CSV):
        ensure_dir(OUT_CSV)
        pd.DataFrame(columns=["date", "value"]).to_csv(OUT_CSV, index=False)
        print("naaim: wrote placeholder CSV (no data).")


def main():
    ensure_dir(OUT_CSV)

    txt = get_text_with_fallbacks(DEFAULT_URLS)
    df = parse_csv_text(txt) if txt else None

    if df is not None and not df.empty:
        df.to_csv(OUT_CSV, index=False)
        print(f"saved {OUT_CSV}, rows={len(df)}")
        return

    # 到这一步说明都失败了：保留旧文件，否则写占位
    if load_prev_csv(OUT_CSV) is not None:
        print("naaim: all sources failed; keep previous file.")
    else:
        write_placeholder_when_needed()


if __name__ == "__main__":
    main()
