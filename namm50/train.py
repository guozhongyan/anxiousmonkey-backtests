
#!/usr/bin/env python3
import os, json, sys
from datetime import datetime, timezone

# robust repo-root detection
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ""))

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def build_dummy_model():
    # Placeholder — replace with real training artifacts as needed
    return {
        "as_of": now_iso(),
        "model": "NAMM-50",
        "version": "0.1.0",
        "latest": True,
        "weights": {
            "naaim_exposure": 0.6,
            "fred_macro": 0.4
        }
    }

def write_model(payload: dict):
    # We publish to two locations to guarantee GitHub Pages availability:
    # 1) docs/models/namm50.json (nested)
    # 2) docs/namm50.json (flat namespace, easy to fetch at /namm50.json)
    out_nested = os.path.join(REPO_ROOT, "docs", "models", "namm50.json")
    out_flat = os.path.join(REPO_ROOT, "docs", "namm50.json")
    for path in (out_nested, out_flat):
        ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":" ))
        print(f"wrote {path}")

def main():
    model = build_dummy_model()
    write_model(model)

if __name__ == "__main__":
    main()
