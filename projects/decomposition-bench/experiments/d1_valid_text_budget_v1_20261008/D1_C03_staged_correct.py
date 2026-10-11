def _call_key(args,kwargs):
    return tuple(args),tuple(sorted(kwargs.items()))

def _compute(args,kwargs):
    return sum(args)+sum(kwargs.values())
def solve(payload):
    from collections import OrderedDict
    cache=OrderedDict();computations=0;output=[]
    for op in payload['operations']:
        if op['op']=='clear': cache.clear();result=None
        else:
            args,kwargs=op.get('args',[]),op.get('kwargs',{})
            canonical_key=_call_key(args,kwargs)
            cache_key=canonical_key
            if cache_key in cache:
                result=cache[cache_key];cache.move_to_end(cache_key)
            else:
                result=_compute(args,kwargs);computations+=1
                if payload['capacity']>0:
                    if len(cache)==payload['capacity']:cache.popitem(last=False)
                    cache[cache_key]=result
        output.append({'result':result,'computations':computations,'size':len(cache)})
    return output
