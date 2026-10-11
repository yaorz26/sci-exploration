from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from more_itertools import more
API_CALLS = {'map_reduce': 0}
_map_reduce = more.map_reduce
def counted_map_reduce(*args, **kwargs):
    API_CALLS['map_reduce'] += 1
    return _map_reduce(*args, **kwargs)
more.map_reduce = counted_map_reduce

def solve(data):
    def reduce(values):
        base = min(values)
        normalized = [v - base for v in values]
        return normalized, sum(normalized)
    reduced = more.map_reduce(data['items'], keyfunc=lambda x: x['group'],
                              valuefunc=lambda x: x['value'], reducefunc=reduce)
    # 顺序来自新任务要求，显式从输入获取，不依赖原API未声明的返回顺序。
    order = list(dict.fromkeys(x['group'] for x in data['items']))
    return {'groups': [{'group': key, 'normalized': reduced[key][0], 'total': reduced[key][1]}
                       for key in order if reduced[key][1] >= data['threshold']]}
