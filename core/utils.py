import os
import json
from datetime import datetime, timezone

def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist (no error if already present)."""
    if not path:
        return
    os.makedirs(path, exist_ok=True)

def ts_now_iso() -> str:
    """UTC timestamp in ISO-8601 with trailing Z."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _default(o):
    """JSON serializer for objects not serializable by default json code."""
    try:
        import numpy as np  # lazy
        if isinstance(o, (np.generic,)):
            return o.item()
    except Exception:
        pass
    try:
        import pandas as pd  # lazy
        if hasattr(o, "to_dict"):
            return o.to_dict(orient="records")  # DataFrame-like
        if hasattr(o, "tolist"):
            return o.tolist()
    except Exception:
        pass
    if hasattr(o, "__dict__"):
        return o.__dict__
    return str(o)

def write_json(path: str, data, indent: int = 2, **kwargs) -> None:
    """Write JSON with sensible defaults.
    Accepts an 'indent' kwarg for backward compatibility.
    """
    d = os.path.dirname(path)
    if d:
        ensure_dir(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, default=_default, **kwargs)

def to_json_ready(obj):
    """Best-effort conversion of common scientific types to JSON-serializable."""
    try:
        import numpy as np  # lazy
        if isinstance(obj, (np.generic,)):
            return obj.item()
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
    except Exception:
        pass
    try:
        import pandas as pd  # lazy
        if hasattr(obj, "to_dict"):
            return obj.to_dict(orient="records")
        if hasattr(obj, "tolist"):
            return obj.tolist()
    except Exception:
        pass
    if isinstance(obj, (set,)):
        return list(obj)
    return obj

def zscore(arr):
    """Simple z-score; works with list/tuple/numpy/pandas."""
    try:
        import numpy as np
        a = np.asarray(arr, dtype=float)
        if a.size == 0:
            return a
        m = a.mean()
        s = a.std() if a.std() != 0 else 1.0
        return (a - m) / s
    except Exception:
        # fallback scalar
        try:
            vals = [float(x) for x in arr]
            m = sum(vals)/len(vals)
            var = sum((x-m)**2 for x in vals)/len(vals)
            s = var**0.5 or 1.0
            return [(x-m)/s for x in vals]
        except Exception:
            return arr