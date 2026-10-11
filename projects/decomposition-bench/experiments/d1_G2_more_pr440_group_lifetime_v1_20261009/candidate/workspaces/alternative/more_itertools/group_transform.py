"""手写的独立模块组织；组变换在当前组有效期间完成。"""
from itertools import groupby

def transform_groups(iterable, keyfunc=None, valuefunc=None, reducefunc=None):
    for key, group in groupby(iterable, keyfunc):
        values = map(valuefunc, group) if valuefunc else group
        yield key, reducefunc(values) if reducefunc else values
