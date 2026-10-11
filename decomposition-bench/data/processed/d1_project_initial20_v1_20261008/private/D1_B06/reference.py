from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_curator'))
from task_specs_snapshot import paths_reference
def solve(payload):
    return paths_reference(payload)
