"""
core.utils — shim that re-exports tools.utils and provides safe fallbacks.
This lets legacy imports like `from core.utils import ts_now_iso` work
without editing existing scripts.
"""
from __future__ import annotations
try:
    from tools.utils import *  # type: ignore
except Exception:
    import os, json
    from datetime import datetime, timezone
    from typing import Any, Iterable, Sequence
    def ensure_dir(path: str | os.PathLike) -> None:
        p = os.fspath(path)
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
    def ts_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    def to_json_ready(obj: Any) -> Any:
        return obj
    def write_json(path: str | os.PathLike, obj: Any) -> None:
        ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    def rolling_sharpe(series: Sequence[float], window: int = 252) -> float:
        data = list(series)[-window:] if len(series) > window else list(series)
        n = len(data)
        if n <= 1:
            return 0.0
        mu = sum(data) / n
        var = sum((x - mu) ** 2 for x in data) / (n - 1)
        sd = var ** 0.5 if var > 0 else 0.0
        return 0.0 if sd == 0 else (mu / sd) * (252 ** 0.5)
    def zscore(x: Iterable[float]) -> list[float]:
        data = list(map(float, x))
        if not data: return []
        mu = sum(data)/len(data)
        var = sum((v-mu)**2 for v in data)/max(1, len(data)-1)
        sd = (var ** 0.5) if var>0 else 1.0
        return [(v-mu)/sd for v in data]
