import os, json, time
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
(DOCS_DIR / "models").mkdir(parents=True, exist_ok=True)

MODEL_JSON = DOCS_DIR / "models" / "namm50.json"

def utc_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def load_weights():
    # Minimal safe defaults; real training code can overwrite this function later.
    # Keep the shape/keys stable so frontends don't break.
    return {
        "NAAM": 1.0,
        "FRED": 0.0,
        "NDX50": 0.0,
        "CHINA": 0.0
    }

def main():
    payload = {
        "as_of": utc_iso(),
        "model": "NAMM-50",
        "version": "v0.1-hotfix",
        "weights": load_weights(),
        "latest": {
            "note": "Hotfix writes model JSON to docs/models/namm50.json"
        }
    }
    tmp = MODEL_JSON.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":" ))
    tmp.replace(MODEL_JSON)
    print(f"wrote {MODEL_JSON}")

if __name__ == "__main__":
    main()