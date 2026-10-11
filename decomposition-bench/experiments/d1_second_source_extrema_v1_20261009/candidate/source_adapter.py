import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "sources"))
import more_itertools

def solve(payload):
    low, high = more_itertools.minmax(payload["data"])
    return {"minimum": low, "maximum": high}
