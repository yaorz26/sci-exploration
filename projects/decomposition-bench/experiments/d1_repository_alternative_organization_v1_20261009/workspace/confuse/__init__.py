"""Painless YAML configuration.
"""

from __future__ import division, absolute_import, print_function

__version__ = '1.4.0'

from .exceptions import * # NOQA
from .util import * # NOQA
from .yaml_util import * # NOQA
from .sources import * # NOQA
from .templates import * # NOQA
from .core import * # NOQA


# 源目录功能的单模块兼容实现；原sources/templates/core不修改。
import copy as _d1_copy
import os as _d1_os

_d1_source_init = ConfigSource.__init__
_d1_yaml_init = YamlSource.__init__
_d1_filename_init = Filename.__init__
_d1_filename_value = Filename.value


def _d1_init_source(self, value, filename=None, default=False, base_for_paths=False):
    _d1_source_init(self, value, filename, default)
    self.base_for_paths = bool(base_for_paths) if filename is not None else False


def _d1_init_yaml(self, filename=None, default=False, base_for_paths=False,
                  optional=False, loader=yaml_util.Loader):
    _d1_yaml_init(self, filename=filename, default=default, optional=optional, loader=loader)
    self.base_for_paths = bool(base_for_paths) if self.filename is not None else False


def _d1_init_filename(self, default=REQUIRED, cwd=None, relative_to=None,
                      in_app_dir=False, in_source_dir=False):
    _d1_filename_init(self, default=default, cwd=cwd, relative_to=relative_to, in_app_dir=in_app_dir)
    self.in_source_dir = in_source_dir


def _d1_filename(self, view, template=None):
    # cwd/relative_to及无值/类型错误继续由原API处理。
    if self.cwd is not None or self.relative_to is not None:
        return _d1_filename_value(self, view, template)
    try:
        value, source = view.first()
    except NotFoundError:
        return _d1_filename_value(self, view, template)
    source_relative = source.filename and (
        self.in_source_dir or (source.base_for_paths and not self.in_app_dir)
    )
    if source_relative:
        scoped = _d1_copy.copy(self)
        scoped.cwd = _d1_os.path.dirname(source.filename)
        return _d1_filename_value(scoped, view, template)
    return _d1_filename_value(self, view, template)


def _d1_set_file(self, filename, base_for_paths=False):
    self.set(YamlSource(filename, base_for_paths=base_for_paths, loader=self.loader))


ConfigSource.__init__ = _d1_init_source
YamlSource.__init__ = _d1_init_yaml
Filename.__init__ = _d1_init_filename
Filename.value = _d1_filename
Configuration.set_file = _d1_set_file
