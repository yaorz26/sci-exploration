"""P93一个原输入，检验底层状态观察是否限制合法委托组织。"""
import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repository_patch_entry import digest, save_new, tree_hashes

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_delegated_state_oracle_v2_20261009"

PROXY = '''

class TTLCache(Cache):
    """研究控制：外部缓存委托给完整内部TTLCache；状态不在外层Cache。"""
    def __init__(self, maxsize, ttl, timer=time.monotonic, getsizeof=None):
        Cache.__init__(self, maxsize, getsizeof)
        self._inner = _InnerTTLCache(maxsize, ttl, timer, getsizeof)
    def __getitem__(self, key):
        return self._inner[key]
    def __setitem__(self, key, value):
        self._inner[key] = value
    def __delitem__(self, key):
        del self._inner[key]
    def __iter__(self):
        return iter(self._inner)
    def __len__(self):
        return len(self._inner)
    def __contains__(self, key):
        return key in self._inner
    def __repr__(self):
        return repr(self._inner)
    @property
    def currsize(self):
        return self._inner.currsize
    @property
    def timer(self):
        return self._inner.timer
    @property
    def ttl(self):
        return self._inner.ttl
    def expire(self, time=None):
        return self._inner.expire(time)
    def popitem(self):
        return self._inner.popitem()
    def clear(self):
        return self._inner.clear()
'''


def worker(workspace):
    sys.path.insert(0, str(workspace))
    import cachetools
    from cachetools import Cache, TTLCache
    if not Path(cachetools.__file__).resolve().is_relative_to(workspace):
        raise RuntimeError("工作区导入错误")
    class Clock:
        value = 0
        def __call__(self):
            return self.value
    clock = Clock()
    cache = TTLCache(maxsize=20, ttl=4, timer=clock, getsizeof=lambda value: 2)
    cache["a"] = 1
    clock.value = 2
    cache["b"] = 2
    result = cache.expire(4)
    def base_snapshot():
        return {"items": sorted([[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)]),
                "size": Cache.currsize.fget(cache)}
    def public_snapshot():
        keys = list(cache)
        return {"items": sorted([[key, cache[key]] for key in keys]),
                "length": len(cache), "size": cache.currsize}
    before_base = base_snapshot()
    before_public = public_snapshot()
    pairs = sorted([[key, value] for key, value in result])
    after_base = base_snapshot()
    after_public = public_snapshot()
    expected_public = {"items": [["b", 2]], "length": 1, "size": 2}
    expected_base = {"items": [["b", 2]], "size": 2}
    return {"timer_during_observation": clock.value, "expiry_deadlines": {"a": 4, "b": 6},
            "returned_pairs": pairs, "before_base": before_base, "before_public": before_public,
            "after_base": after_base, "after_public": after_public,
            "return_pass": pairs == [["a", 1]],
            "public_contract_pass": pairs == [["a", 1]] and before_public == after_public == expected_public,
            "original_base_after_consumption_pass": pairs == [["a", 1]] and after_base == expected_base,
            "scope": "原boundary_mixed单输入/API；不证明全库代理等价；手工组织非模型"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.workspace.resolve()), ensure_ascii=False))
        return
    OUT.mkdir(exist_ok=False)
    saved = ROOT / "experiments/d1_cache_expiry_repository_task_v1_20261009"
    feature = saved / "feature/src/cachetools"
    report = saved / "execution_v1/research_controls/report_only/cachetools"
    predictions = {"complete": [True, True], "delegated": [True, False],
                   "report_only": [False, False], "deferred": [False, True]}
    for name in predictions:
        workspace = OUT / "workspaces" / name
        shutil.copytree(report if name == "report_only" else feature, workspace / "cachetools")
        file = workspace / "cachetools/__init__.py"
        source = file.read_text(encoding="utf-8")
        if name == "delegated":
            node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "TTLCache")
            lines = source.splitlines(keepends=True)
            block = "".join(lines[node.lineno - 1:node.end_lineno])
            changed = re.sub(r"\bTTLCache\b", "_InnerTTLCache", block)
            source = "".join(lines[:node.lineno - 1]) + changed + "".join(lines[node.end_lineno:]) + PROXY
            file.write_text(source, encoding="utf-8", newline="\n")
        elif name == "deferred":
            source += '''

_research_expire = TTLCache.expire
def _deferred_expire(self, time=None):
    def consume():
        yield from _research_expire(self, time)
    return consume()
TTLCache.expire = _deferred_expire
'''
            file.write_text(source, encoding="utf-8", newline="\n")
    frozen = {"time": datetime.now(timezone.utc).isoformat(), "input": {"puts": [[0, "a", 1], [2, "b", 2]],
              "ttl": 4, "expire": 4, "observe_timer": 2, "getsizeof": 2},
              "predictions_public_and_original_base": predictions,
              "workspaces": {name: tree_hashes(OUT / "workspaces" / name) for name in predictions},
              "program_sha256": digest(Path(__file__)), "model_calls": 0,
              "source_input": "P88原boundary_mixed；独特新增输入0"}
    save_new(OUT / "freeze_before_execution.json", frozen)
    rows = []
    for name, expected in predictions.items():
        workspace = OUT / "workspaces" / name
        proc = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__)),
            "--worker", "--workspace", str(workspace)], capture_output=True, text=True, encoding="utf-8", timeout=10)
        save_new(OUT / (name + "_process.json"), {"returncode": proc.returncode,
                  "stdout": proc.stdout, "stderr": proc.stderr})
        actual = json.loads(proc.stdout) if proc.returncode == 0 else {"environment_error": True}
        save_new(OUT / (name + "_actual.json"), actual)
        observed = [actual.get("public_contract_pass"), actual.get("original_base_after_consumption_pass")]
        row = {"name": name, "expected": expected, "observed": observed,
               "prediction_match": observed == expected, "actual_path": name + "_actual.json"}
        rows.append(row)
        if tree_hashes(workspace) != frozen["workspaces"][name]:
            raise RuntimeError("执行修改了候选工作区")
    summary = {"organizations": 4, "reused_public_inputs": 1, "new_unique_inputs": 0,
               "model_calls": 0, "api_calls": 0, "human_reviews": 0, "rows": rows,
               "all_predictions_match": all(r["prediction_match"] for r in rows),
               "scope": "一个任务/API的存储位置误拒反例；不推全库/模型效果；原oracle不改"}
    save_new(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    if not summary["all_predictions_match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
