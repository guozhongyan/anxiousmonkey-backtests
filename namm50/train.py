
from core.utils import ensure_dir, write_json, ts_now_iso

def main():
    ensure_dir('docs/models')
    model = {
        "as_of": ts_now_iso(),
        "model": "NAMM-50",
        "version": "v0.1-hotfix",
        "weights": {"NAAM": 1.0, "FRED": 0.0, "NDX50": 0.0, "CHINA": 0.0},
        "latest": {"note": "Hotfix writes model JSON to docs/models/namm50.json"}
    }
    write_json('docs/models/namm50.json', model, indent=2)
    print('model json ready')

if __name__ == '__main__':
    main()
