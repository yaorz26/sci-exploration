"""Build and audit a versioned D1 prototype from curator-only specifications."""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import task_specs
from bounded_execution import evaluate

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def alternate_source(function):
    collected = {}
    def collect(fn):
        if fn.__name__ in collected:
            return
        source = inspect.getsource(fn)
        collected[fn.__name__] = source
        used = {node.id for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Name)}
        for name in used:
            dependency = fn.__globals__.get(name)
            if inspect.isfunction(dependency) and dependency.__module__ in ("task_specs", "task_specs_expansion"):
                collect(dependency)
    collect(function)
    return ("from collections import OrderedDict\n\n" + "\n\n".join(collected.values())
            + f"\n\ndef solve(payload):\n    return {function.__name__}(payload)\n")

def run_candidate(candidate, cases, output_dir):
    return evaluate(candidate, cases)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    ex = task_specs.EXPERIMENT_ROOT
    dataset = ex / "data/processed" / args.version
    experiment = ex / "experiments" / args.version
    dataset.mkdir(parents=True, exist_ok=False)
    public_dir, private_dir = dataset / "public", dataset / "private"
    curator_dir = private_dir / "_curator"
    curator_dir.mkdir(parents=True)
    snapshot_source = Path(task_specs.__file__).read_text(encoding="utf-8").replace(
        "EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]",
        "EXPERIMENT_ROOT = Path(__file__).resolve().parents[5]")
    (curator_dir / "task_specs_snapshot.py").write_text(snapshot_source, encoding="utf-8")
    expansion_source = Path(task_specs.__file__).with_name("task_specs_expansion.py").read_text(encoding="utf-8").replace(
        "EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]",
        "EXPERIMENT_ROOT = Path(__file__).resolve().parents[5]")
    (curator_dir / "task_specs_expansion.py").write_text(expansion_source, encoding="utf-8")
    shutil.copyfile(Path(__file__), curator_dir / "build_dataset_snapshot.py")
    manifest, checks = [], []
    for spec in task_specs.TASKS:
        task_id = spec["id"]
        public, private = public_dir/task_id, private_dir/task_id
        public.mkdir(parents=True); private.mkdir(parents=True)
        upstream = json.loads((ex/f"data/raw/d1_project_v1_20261008/manifests/{spec['repo']}.json").read_text(encoding="utf-8"))
        file_path = task_specs.SOURCE_ROOT/spec["repo"]/spec["file"]
        definitions = [node for node in ast.parse(file_path.read_text(encoding="utf-8")).body
                       if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == spec["symbol"]]
        source = {"repository":upstream["repository"], "commit":upstream["commit"],
                  "license":upstream["license_review"]["license"], "file":spec["file"],
                  "symbol":spec["symbol"], "line":definitions[0].lineno,
                  "source_sha256":hashlib.sha256(file_path.read_bytes()).hexdigest(),
                  "license_sha256":upstream["license_review"]["sha256"],
                  "contamination_risk":"unknown"}
        source["additional_symbols"] = []
        for extra_file, extra_symbol in spec.get("source_symbols", []):
            extra_path = task_specs.SOURCE_ROOT/spec["repo"]/extra_file
            nodes = [node for node in ast.parse(extra_path.read_text(encoding="utf-8")).body
                     if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == extra_symbol]
            assert len(nodes) == 1, (extra_file, extra_symbol)
            source["additional_symbols"].append({"file":extra_file,"symbol":extra_symbol,
                "line":nodes[0].lineno,"source_sha256":hashlib.sha256(extra_path.read_bytes()).hexdigest()})
        public_cases = [{"case_id":f"public_{i+1}","input":p,"expected":task_specs.MANUAL_PUBLIC_OUTCOMES[task_id][i]}
                        for i,p in enumerate(spec["public"])]
        private_cases=[]
        for i,p in enumerate(spec["private"]):
            private_cases.append({"case_id":f"hidden_{i+1}","input":p,"expected":task_specs.outcome(spec["reference"],p)})
        disagreements=[]
        for case in public_cases + private_cases:
            reference = task_specs.outcome(spec["reference"],case["input"])
            alternate = task_specs.outcome(spec["alternate"],case["input"])
            if reference != case["expected"] or alternate != case["expected"]:
                disagreements.append({"case_id":case["case_id"],"input":case["input"],"expected":case["expected"],"reference":reference,"alternate":alternate})
        write_json(private/"oracle_crosscheck.json",{"disagreements":disagreements,"manual_public_anchors":len(public_cases),"comparison":"上游实现与另一种纯标准库实现；同一作者，不等于独立审查"})
        write_json(public/"public_tests.json",public_cases)
        write_json(private/"private_tests.json",private_cases)
        (public/"starter.py").write_text("def solve(payload):\n    raise NotImplementedError('implement external behavior')\n",encoding="utf-8")
        task = {"task_id":task_id,"requirement":spec["requirement"],"entry_point":"solve(payload)",
                "language":"Python","allowed_libraries":"仅Python标准库",
                "public_examples":[{"input":case["input"], **({"output":case["expected"]["value"]}
                    if "value" in case["expected"] else {"raises":case["expected"]["error"]})} for case in public_cases],
                "general_contract":"不得修改输入payload及其嵌套内容。测试输入符合已声明的字段与类型，明确要求的异常情形除外；不要求验证未声明的域外输入。",
                "internal_decomposition":"自由选择，不给定helper名称或数量"}
        write_json(public/"task.json",task)
        record = {"task_id":task_id,"name":spec["name"],"source":source,
                  "requirement_origin":"上游公开API文档/说明为主，适配器范围与边界补充；已查看实现，需独立泄漏审查",
                  "adaptation":"统一JSON入口和返回值，保留所选功能；不作为完整仓库任务",
                  "split":"development" if spec["repo"] in ["boltons","cachetools"] else "reserve",
                  "structure":{"kind":spec["kind"],"shared_state":spec["state"],"dependency_evidence":spec["dependency"],"independent_test_evidence":spec["independent_stage_test"],"status":"单人预标注，尚未取得独立一致性统计"},
                  "function_family":spec["family"],"public_cases":len(public_cases),"private_cases":len(private_cases),
                  "status":"候选原型，非冻结确认集","authoring_seed":20261008}
        state, scope, dependencies, testability, evidence = task_specs.STRUCTURE_V2[task_id]
        record["structure_v2"] = {"schema_version":"0.2","cross_operation_state":state,
            "state_scope":scope,"behavior_dependencies":dependencies,"separate_behavior_testability":testability,
            "evidence":evidence,"status":"单人初标；依据外部契约，未取得独立人工一致性统计",
            "legacy_author_description":record["structure"]}
        record["related_families"] = spec.get("related_families", [])
        write_json(private/"metadata.json",record)
        shutil.copyfile(task_specs.SOURCE_ROOT/spec["repo"]/"LICENSE",private/"UPSTREAM_LICENSE.txt")
        reference_module = "task_specs_snapshot" if spec["reference"].__module__ == "task_specs" else "task_specs_expansion"
        reference_source = "from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_curator'))\nfrom " + reference_module + " import " + spec["reference"].__name__ + "\ndef solve(payload):\n    return " + spec["reference"].__name__ + "(payload)\n"
        (private/"reference.py").write_text(reference_source,encoding="utf-8")
        alternate = alternate_source(spec["alternate"])
        (private/"alternate.py").write_text(alternate,encoding="utf-8")
        full_cases=public_cases+private_cases
        write_json(private/"all_tests.json",full_cases)
        variants = {"starter":public/"starter.py", "alternate":private/"alternate.py", "reference":private/"reference.py"}
        wrong_empty=private/"wrong_empty.py"; wrong_empty.write_text("def solve(payload):\n    return []\n",encoding="utf-8")
        wrong_last=private/"wrong_drop_last.py"; wrong_last.write_text(alternate+"\n_original = solve\ndef solve(payload):\n    value = _original(payload)\n    if isinstance(value, (list, str)) and value: return value[:-1]\n    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])\n    return value\n",encoding="utf-8")
        lookup={json.dumps(case['input'],sort_keys=True,ensure_ascii=False):case['expected'] for case in public_cases}
        wrong_public=private/"wrong_public_lookup.py"; wrong_public.write_text("import json\n_LOOKUP = "+repr(lookup)+"\ndef solve(payload):\n    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})\n    if 'error' in found: raise ValueError('public case')\n    return found['value']\n",encoding="utf-8")
        variants.update({"wrong_empty":wrong_empty,"wrong_drop_last":wrong_last,"wrong_public_lookup":wrong_public})
        audit={"task_id":task_id,"oracle_disagreements":len(disagreements),"implementations":{},"reference_repeats":[]}
        for name,path in variants.items():
            audit["implementations"][name]=run_candidate(path,private/"all_tests.json",experiment)
        for _ in range(3):
            audit["reference_repeats"].append(run_candidate(private/"reference.py",private/"all_tests.json",experiment))
        audit["reference_stable_3"] = all(row["all_pass"] for row in audit["reference_repeats"])
        audit["starter_fails"] = not audit["implementations"]["starter"]["all_pass"]
        audit["alternate_passes"] = audit["implementations"]["alternate"]["all_pass"]
        audit["wrong_implementations_rejected"] = all(not audit["implementations"][name]["all_pass"] for name in ["wrong_empty","wrong_drop_last","wrong_public_lookup"])
        audit["quality_pass"] = not disagreements and all(audit[key] for key in ["reference_stable_3","starter_fails","alternate_passes","wrong_implementations_rejected"])
        write_json(private/"quality_audit.json",audit)
        record["quality_pass"]=audit["quality_pass"]
        manifest.append(record); checks.append(audit)
        print(json.dumps({"task_id":task_id,"quality_pass":audit["quality_pass"],"oracle_disagreements":len(disagreements),"cases":len(full_cases)},ensure_ascii=False),flush=True)
    result={"version":args.version,"built_at":datetime.now(timezone.utc).isoformat(),"tasks":manifest,
            "task_count":len(manifest),"quality_pass_count":sum(row["quality_pass"] for row in manifest),
            "public_case_count":sum(row["public_cases"] for row in manifest),"private_case_count":sum(row["private_cases"] for row in manifest),
            "source_repository_count":len({row["source"]["repository"] for row in manifest}),
            "split_policy":"按来源仓库隔离；开发boltons/cachetools，储备more-itertools/confuse；未冻结",
            "independent_review":"尚未完成","state":"候选原型"}
    write_json(dataset/"manifest.json",result)
    write_json(experiment/"quality_summary.json",result)
    hashes={str(path.relative_to(dataset)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(dataset.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}
    write_json(experiment/"dataset_hashes.json",hashes)

if __name__ == "__main__":
    main()
