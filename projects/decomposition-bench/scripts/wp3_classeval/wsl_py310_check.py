"""WP3 补充：在 WSL（Python 3.10 + NumPy 1.x）里验证依赖旧版 NumPy 语义的题目。

背景：ClassEval 建于 NumPy 1.x 时代，ClassEval_51 的参考实现依赖 `float(数组)` 的宽松转换，
该行为在 NumPy 2.x 被收紧（TypeError）。本机 Windows 侧只有 Python 3.13（无 numpy<2 的轮子），
因此用 WSL 的 Python 3.10 建一个 numpy<2 的 venv 来交叉验证。

只跑参考实现与官方测试，不调用任何生成模型。
"""
import os
import subprocess

VENV = "/mnt/d/yaorz/research/decomposition-bench/.venvs/wsl_py310"
BASE = "/mnt/d/yaorz/research/decomposition-bench/experiments/wp3_classeval/work"
TASKS = ["ClassEval_51"]

SCRIPT = f"""
set -u
RP={VENV}
if [ ! -x "$RP/bin/python" ]; then
  python3 -m venv "$RP"
fi
"$RP/bin/python" -m pip install -q --upgrade pip
"$RP/bin/python" -m pip install -q "numpy<2"
"$RP/bin/python" -c "import numpy,sys;print('numpy',numpy.__version__,'| py',sys.version.split()[0])"
for T in {' '.join(TASKS)}; do
  cd "{BASE}/$T"
  "$RP/bin/python" ref_full.py > /tmp/$T.log 2>&1
  echo "$T EXIT=$?"
  tail -4 /tmp/$T.log
done
"""


def main() -> None:
    env = {k: v for k, v in os.environ.items() if k.lower() not in ("http_proxy", "https_proxy", "all_proxy")}
    p = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu-22.04", "--", "bash", "-lc", SCRIPT],
        capture_output=True,
        text=True,
        timeout=1200,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    print("rc:", p.returncode)
    print((p.stdout or "").strip()[-2000:])
    if p.stderr:
        print("stderr:", (p.stderr or "").strip()[:500])


if __name__ == "__main__":
    main()
