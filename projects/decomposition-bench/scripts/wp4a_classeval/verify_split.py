"""WP4A 校验：对冻结的探索集 24 题验证"公开/私有按方法切分"不影响参考实现通过。

判定：对每题分别跑
  ① 参考实现 + 公开测试   → 必须通过
  ② 参考实现 + 公开 + 私有测试（全量） → 必须通过
两者都通过，说明切分没有破坏参考实现的正确性；私有测试单独保存在 private/ 下，不进入模型可读目录。
"""
import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(r"D:\yaorz\research\projects\decomposition-bench")
OUT = ROOT / "data/processed/classeval_v1"
SPLITS = ROOT / "data/splits/classeval_v1/frozen_manifest.json"
WORK = ROOT / "experiments/wp4a_classeval_regression/split_check"
VENV_PY = ROOT / ".venvs/bigcodebench_fast0/Scripts/python.exe"
os.environ.setdefault("NLTK_DATA", r"D:\yaorz\research\.cache\nltk_data")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    tasks = [json.loads(l) for l in (OUT / "tasks_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    priv = {json.loads(l)["task_id"]: json.loads(l)["private_tests"]
            for l in (OUT / "private/private_tests.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    exploratory = json.loads(SPLITS.read_text(encoding="utf-8"))["exploratory_set"]["task_ids"]
    by_id = {t["task_id"]: t for t in tasks}

    results = []
    for tid in exploratory:
        t = by_id[tid]
        d = WORK / tid
        d.mkdir(parents=True, exist_ok=True)
        pub_only = t["reference_impl"].rstrip() + "\n\n" + t["public_tests"].rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
        full = t["reference_impl"].rstrip() + "\n\n" + t["public_tests"].rstrip() + "\n\n" + priv[tid].rstrip() + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
        (d / "ref_public_only.py").write_text(pub_only, encoding="utf-8")
        (d / "ref_full.py").write_text(full, encoding="utf-8")
        row = {"task_id": tid, "layer": t["metadata"]["layer"],
               "public_available": t["split"]["public_available"], "runs": []}
        if not t["split"]["public_available"]:
            row["ok"] = None
            row["note"] = "公开测试不可用（public_available=False），公开选择规则对该题不适用"
            results.append(row)
            print(f"  {tid} ({row['layer']}): 公开测试不可用，跳过")
            continue
        for name, fn in [("public_only", "ref_public_only.py"), ("full", "ref_full.py")]:
            t0 = time.time()
            p = subprocess.run([str(VENV_PY), fn], cwd=str(d), capture_output=True, text=True, timeout=240)
            row["runs"].append({"case": name, "exit_code": p.returncode, "seconds": round(time.time() - t0, 2),
                                "ok": p.returncode == 0, "tail": ((p.stdout or "") + (p.stderr or ""))[-300:]})
        row["ok"] = all(r["ok"] for r in row["runs"])
        results.append(row)
        print(f"  {tid} ({row['layer']}): public_only={row['runs'][0]['exit_code']} full={row['runs'][1]['exit_code']}")

    summary = {"n": len(results), "all_ok": sum(1 for r in results if r["ok"]),
               "skipped_no_public": [r["task_id"] for r in results if r["ok"] is None],
               "failed": [r["task_id"] for r in results if r["ok"] is False]}
    (WORK / "split_check.json").write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n汇总:", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
