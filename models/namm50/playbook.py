import json
from core.utils import ts_now_iso, write_json

SIG = "docs/signals_namm50.json"
OUT = "docs/playbook_namm50.json"


def plan(s):
    if s >= 1.0:
        return ("加仓", "Beta +30%", "高胜率窗口，顺势持有")
    if s <= -1.0:
        return ("降仓", "Beta -30%", "回避风险，等待拐点")
    return ("观望", "中性", "轻仓/择机")


def main():
    try:
        sig = json.load(open(SIG, "r", encoding="utf-8"))
        score = float(sig.get("score", 0.0))
    except Exception:
        score = 0.0
    action, risk, note = plan(score)
    payload = {
        "as_of": ts_now_iso(),
        "playbook": {
            "3D": {"action": "观望", "note": "等待确认", "risk": "中性"},
            "12D": {"action": "中性定位", "note": "择机加减", "risk": "中等"},
            "1M": {"action": action, "note": note, "risk": risk},
        },
    }
    write_json(OUT, payload)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
