from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_curator'))
from task_specs_expansion import schema_reference
def solve(payload):
    return schema_reference(payload)
