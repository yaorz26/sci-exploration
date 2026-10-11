from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source'))
from boltons import iterutils
SEARCH_RESULT = True
API_CALLS = {'remap': 0, 'research': 0}
_remap, _research = iterutils.remap, iterutils.research
def counted_remap(*args, **kwargs):
    API_CALLS['remap'] += 1
    return _remap(*args, **kwargs)
def counted_research(*args, **kwargs):
    API_CALLS['research'] += 1
    return _research(*args, **kwargs)
iterutils.remap = counted_remap
iterutils.research = counted_research

def solve(data):
    def visit(path, key, value):
        if value is None and data['drop_null']:
            return False
        if type(value) is int:
            return key, value * data['factor']
        return key, value
    tree = iterutils.remap(data['tree'], visit=visit)
    found = iterutils.research(
        tree if SEARCH_RESULT else data['tree'],
        query=lambda p, k, v: type(v) is int and v >= data['threshold'],
        reraise=True)
    return {'tree': tree, 'matches': [{'path': list(p), 'value': v} for p, v in found]}
