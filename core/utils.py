
# Generated hotfix 2025-08-13 19:56:21Z
import os, json, datetime

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def ts_now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def write_json(path: str, data, indent=2):
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def zscore(x, mean, std):
    try:
        return (x - mean) / std if std else 0.0
    except Exception:
        return 0.0
