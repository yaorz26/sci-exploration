"""用保持原三文件的单模块实现检查评价器的代码组织偏好。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/parent"
EVALUATOR = ROOT / "experiments/d1_runnable_repository_task_v2_20261009/candidate/evaluate.py"
OUT = ROOT / "experiments/d1_repository_alternative_organization_v1_20261009"
OUT.mkdir(exist_ok=False)
workspace = OUT / "workspace"
shutil.copytree(PARENT / "confuse", workspace / "confuse")
shutil.copy2(PARENT / "LICENSE", workspace / "LICENSE")
patch = r'''

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
'''
init = workspace / "confuse/__init__.py"
with init.open("a", encoding="utf-8") as handle:
    handle.write(patch)
unchanged = {}
for name in ("sources.py", "templates.py", "core.py"):
    old_hash = hashlib.sha256((PARENT / "confuse" / name).read_bytes()).hexdigest()
    new_hash = hashlib.sha256((workspace / "confuse" / name).read_bytes()).hexdigest()
    unchanged[name] = {"parent": old_hash, "alternative": new_hash, "equal": old_hash == new_hash}
freeze = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "organization": "单一__init__.py兼容扩展；保留原sources/templates/core",
    "author": "助手手写，非模型实验和非人类双审",
    "prediction": "同一八项公开诊断8/8；不证明八例之外合法性",
    "unchanged": unchanged,
    "implementation_sha256": hashlib.sha256(init.read_bytes()).hexdigest(),
    "evaluator_sha256": hashlib.sha256(EVALUATOR.read_bytes()).hexdigest(),
    "new_inputs": 0,
    "model_calls": 0,
}
with (OUT / "freeze_before_execution.json").open("x", encoding="utf-8") as handle:
    json.dump(freeze, handle, ensure_ascii=False, indent=2)
proc = subprocess.run([sys.executable, "-B", str(EVALUATOR), "--workspace", str(workspace), "--output", str(OUT / "actual.json")], capture_output=True, text=True, encoding="utf-8", timeout=70)
with (OUT / "process_result.json").open("x", encoding="utf-8") as handle:
    json.dump({"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}, handle, ensure_ascii=False, indent=2)
print(proc.stdout)
if proc.returncode:
    raise SystemExit(proc.returncode)
