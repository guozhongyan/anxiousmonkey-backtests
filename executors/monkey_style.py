import json, numpy as np
from core.utils import ensure_dir, ts_now_iso, write_json

FACT = "docs/factors_namm50.json"
MODL = "docs/models/namm50.json"
SIG  = "docs/signals_namm50.json"
PLAY = "docs/playbook_namm50.json"

def last_z(series):
    if not series: return None
    zs = [row[2] for row in series if len(row)>=3 and row[2] is not None]
    return zs[-1] if zs else None

def main():
    try:
        fx = json.load(open(FACT, "r", encoding="utf-8"))
    except Exception:
        fx = {"factors":{}}
    try:
        md = json.load(open(MODL, "r", encoding="utf-8"))
    except Exception:
        md = {"weights":{"NAAM":1.0,"FRED":0.0,"NDX50":0.0,"CHINA":0.0}}
    w = md.get("weights", {})
    z = {
        "NAAM": last_z(fx.get("factors",{}).get("naaim_exposure",{}).get("series")),
        "FRED": last_z(fx.get("factors",{}).get("fred_macro",{}).get("series")),
        "NDX50":last_z(fx.get("factors",{}).get("ndx_breadth",{}).get("series")),
        "CHINA":last_z(fx.get("factors",{}).get("china_proxy",{}).get("series")),
    }
    z = {k:(0.0 if v is None else float(v)) for k,v in z.items()}
    score = sum((w.get(k,0.0) * z.get(k,0.0)) for k in z.keys())
    stance = "Risk-On" if score >= 0.5 else ("Risk-Off" if score <= -0.5 else "Neutral")
    write_json(SIG, {"as_of": ts_now_iso(), "model":"NAMM-50", "score": score, "stance": stance, "z": z, "weights": w})
    write_json(PLAY, {"as_of": ts_now_iso(),"playbook": {
        "3D": "Wait for signal" if stance=="Neutral" else ("Buy weakness" if stance=="Risk-On" else "Reduce beta"),
        "12D":"Neutral positioning",
        "1M": "Balanced beta" if stance=="Neutral" else ("Add risk" if stance=="Risk-On" else "Hedge with T-Bills"),
    }})
    print(f"signals/playbook updated: score={score:.3f}, stance={stance}")

if __name__ == "__main__":
    main()
