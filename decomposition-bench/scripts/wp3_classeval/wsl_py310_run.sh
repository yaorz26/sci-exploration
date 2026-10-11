#!/usr/bin/env bash
# WP3 补充：在 WSL 用 Python 3.10 + NumPy 1.x 交叉验证依赖旧版语义的题目（ClassEval_51）。
# 由 scripts/wp3_classeval/wsl_py310_check.py 写入并调用；也可直接：wsl -d Ubuntu-22.04 -- bash /mnt/d/.../run.sh
set -u
VENV=/mnt/d/yaorz/research/decomposition-bench/.venvs/wsl_py310
BASE=/mnt/d/yaorz/research/decomposition-bench/experiments/wp3_classeval/work
TASKS="ClassEval_51"

echo "--- 环境 ---"
python3 -V
if [ ! -x "$VENV/bin/python" ]; then
  echo "创建 venv: $VENV"
  python3 -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q "numpy<2"
"$VENV/bin/python" -c "import numpy,sys;print('numpy',numpy.__version__,'| py',sys.version.split()[0])"

echo "--- 逐题跑参考实现 ---"
for T in $TASKS; do
  cd "$BASE/$T" || { echo "$T 目录不存在"; continue; }
  "$VENV/bin/python" ref_full.py > "/tmp/$T.log" 2>&1
  echo "$T EXIT=$?"
  tail -5 "/tmp/$T.log"
done
