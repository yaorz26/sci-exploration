"""只评价一个新增公开YamlSource入口场景；不读取上游测试或隐藏结果。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def worker(workspace):
    workspace = workspace.resolve(strict=True)
    sys.path.insert(0, str(workspace))
    import confuse
    imported = Path(confuse.__file__).resolve()
    if workspace not in imported.parents:
        raise RuntimeError("导入的包不属于待评价工作区")
    root = Path(tempfile.mkdtemp(prefix="d1_pr126_direct_yaml_"))
    app = root / "app"
    source_dir = root / "project" / "settings"
    cwd = root / "working"
    for path in (app, source_dir, cwd):
        path.mkdir(parents=True)
    source_file = source_dir / "config.yaml"
    source_file.write_text("path: assets/a.txt\n", encoding="utf-8")
    original_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        config = confuse.Configuration("d1gap", read=False)
        source = confuse.YamlSource(str(source_file), base_for_paths=True)
        config.add(source)
        observed = config["path"].get(confuse.Filename())
        expected = str(source_dir / "assets" / "a.txt")
        result = {"workspace": str(workspace), "imported_from": str(imported),
                  "expected": expected, "observed": observed,
                  "passed": observed == expected, "exception": None,
                  "scope": "一个公开YamlSource入口场景；不证明全域或模型收益"}
    except Exception as exc:
        result = {"workspace": str(workspace), "imported_from": str(imported),
                  "expected": str(source_dir / "assets" / "a.txt"), "observed": None,
                  "passed": False, "exception": {"type": type(exc).__name__, "message": str(exc)},
                  "scope": "一个公开YamlSource入口场景；不证明全域或模型收益"}
    finally:
        os.chdir(original_cwd)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.workspace), ensure_ascii=False))
        return
    if args.output is None:
        parser.error("需要 --output 保存独占新结果")
    proc = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                           "--worker", "--workspace", str(args.workspace.resolve())],
                          capture_output=True, text=True, encoding="utf-8", timeout=30)
    if proc.returncode:
        result = {"workspace": str(args.workspace.resolve()), "environment_error": True,
                  "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
                  "passed": False, "scope": "一个公开YamlSource入口场景；不证明全域或模型收益"}
    else:
        result = json.loads(proc.stdout)
    result["evaluator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"workspace": args.workspace.name, "passed": result.get("passed"),
                      "exception": result.get("exception")}, ensure_ascii=False))
    if result.get("environment_error"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
