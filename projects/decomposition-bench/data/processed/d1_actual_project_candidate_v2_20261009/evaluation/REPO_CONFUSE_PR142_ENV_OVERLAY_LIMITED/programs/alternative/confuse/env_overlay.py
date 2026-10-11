"""手写的有限域替代组织；不使用PR142工具函数。"""
import os
import yaml
from . import yaml_util
from .sources import ConfigSource

def apply_environment(config, prefix=None, sep='__'):
    prefix = prefix if prefix is not None else config.appname.upper() + '_'
    overlay = {}
    for name, raw in os.environ.items():
        if not name.startswith(prefix):
            continue
        path = name[len(prefix):].lower().split(sep) if sep else [name[len(prefix):].lower()]
        node = overlay
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = yaml.load(raw, Loader=config.loader)
    config.set(ConfigSource(overlay))
