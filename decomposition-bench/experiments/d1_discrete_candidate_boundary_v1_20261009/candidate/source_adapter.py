import math

def _validate(payload):
    if type(payload) is not dict:
        raise TypeError("payload must be a plain dictionary")
    if "data" not in payload:
        raise ValueError("missing data")
    if set(payload) - {"data", "default"}:
        raise ValueError("unexpected field")
    values = payload["data"]
    if type(values) is not list:
        raise TypeError("data must be a list")
    if len(values) > 128:
        raise ValueError("data exceeds 128 items")
    if any(type(value) not in (int, str) for value in values):
        raise TypeError("data items must have exact type int or str")
    default = payload.get("default", None)
    if default is not None and type(default) not in (bool, str, int, float):
        raise TypeError("default must be a JSON scalar")
    if type(default) is float and not math.isfinite(default):
        raise ValueError("default must be finite")
    return values, default

import importlib.util
from pathlib import Path

_source = Path(__file__).resolve().parent / "sources" / "statsutils.py"
_spec = importlib.util.spec_from_file_location("d1_eb09_statsutils", _source)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

def solve(payload):
    values, default = _validate(payload)
    # 数量空域固定0；众数空域按题面default。不是单一上游对象的原契约。
    return {"count": _module.Stats(values, default=0).count,
            "mode": _module.Stats(values, default=default).mode}
