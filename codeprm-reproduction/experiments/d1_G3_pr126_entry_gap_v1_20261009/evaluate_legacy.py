"""评价任意项目包工作区的公开路径功能；只调用外部API。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile


def evaluate(workspace):
    sys.path.insert(0, str(workspace))
    import confuse
    import yaml

    actual_module = Path(confuse.__file__).resolve()
    if not actual_module.is_relative_to(workspace):
        raise RuntimeError("导入的模块不属于待评价工作区")
    rows = []
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="d1_repo_path_") as task_tmp:
        root = Path(task_tmp).resolve()
        app = root / "app"
        srcdir = root / "project" / "settings"
        cwd = root / "working"
        override = root / "override"
        for path in (app, srcdir, cwd, override):
            path.mkdir(parents=True)
        source_file = srcdir / "config.yaml"
        source_file.write_text("path: assets/a.txt\n", encoding="utf-8")
        absolute = root / "absolute" / "file.bin"
        os.environ["D1FEATUREDIR"] = str(app)
        os.chdir(cwd)

        # 期望由公开需求和实际目录构成，不从参考实现采样。
        cases = [
            ("default_file", "config", {}, {}, "file", "relative", app),
            ("source_flag", "config", {"base_for_paths": True}, {}, "file", "relative", srcdir),
            ("template_flag", "config", {}, {"in_source_dir": True}, "file", "relative", srcdir),
            ("app_over_source_flag", "config", {"base_for_paths": True}, {"in_app_dir": True}, "file", "relative", app),
            ("cwd_over_source_flag", "config", {"base_for_paths": True}, {"cwd": str(override)}, "file", "relative", override),
            ("flag_without_filename", "config", {"base_for_paths": True}, {}, "none", "relative", cwd),
            ("absolute_preserved", "config", {"base_for_paths": True}, {}, "file", "absolute", absolute),
            ("file_loader_flag", "set_file", {"base_for_paths": True}, {}, "file", "relative", srcdir),
        ]
        for name, api, source_kwargs, template_kwargs, filename_kind, value_kind, expected_base in cases:
            expected = str(expected_base) if value_kind == "absolute" else str(expected_base / "assets" / "a.txt")
            value = str(absolute) if value_kind == "absolute" else "assets/a.txt"
            try:
                config = confuse.Configuration("d1feature", read=False)
                if api == "set_file":
                    config.set_file(str(source_file), **source_kwargs)
                else:
                    filename = str(source_file) if filename_kind == "file" else None
                    config.add(confuse.ConfigSource({"path": value}, filename=filename, **source_kwargs))
                observed = config["path"].get(confuse.Filename(**template_kwargs))
                rows.append({"case": name, "expected": expected, "actual": observed, "pass": observed == expected})
            except Exception as exc:
                rows.append({"case": name, "expected": expected, "exception": type(exc).__name__, "message": str(exc), "pass": False})
        os.chdir(original_cwd)

    return {
        "workspace": str(workspace),
        "python": platform.python_version(),
        "pyyaml": yaml.__version__,
        "module": str(actual_module),
        "cases": rows,
        "passed": sum(row["pass"] for row in rows),
        "total": len(rows),
        "all_pass": all(row["pass"] for row in rows),
        "scope": "公开研究诊断；非隐藏确认；非模型效果",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve(strict=True)
    if args.worker:
        print(json.dumps(evaluate(workspace), ensure_ascii=False))
        return
    if args.output is None:
        parser.error("需要 --output 保存独占新结果")
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    proc = subprocess.run(
        [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--worker", "--workspace", str(workspace)],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    if proc.returncode:
        result = {"workspace": str(workspace), "environment_error": True, "returncode": proc.returncode, "stderr": proc.stderr}
    else:
        result = json.loads(proc.stdout)
    result["evaluator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key: result.get(key) for key in ("workspace", "passed", "total", "all_pass", "environment_error")}, ensure_ascii=False))
    if result.get("environment_error"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
