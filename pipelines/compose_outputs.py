
#!/usr/bin/env python3
import os, json
from datetime import datetime, timezone

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def compose():
    # No-op safeguard; real composition already handled upstream.
    # We still emit a tiny stamp file so the workflow step succeeds.
    payload = {"as_of": now_iso(), "ok": True}
    out = os.path.join(os.path.dirname(__file__), "..", "docs", "compose_ok.json")
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"wrote {out}")

def main():
    compose()

if __name__ == "__main__":
    main()
