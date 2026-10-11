"""审计：刚才失败的 bash 命令是否在工作区留下副作用。

背景：2026-09-28 13:40 左右，一条 `python -c "..."` 命令的字符串内容里含有反引号，
被 bash 当成命令替换执行，导致若干 md 文件被 bash 以脚本方式解释（产生大量
"command not found"）。本脚本用于核实该次误执行是否创建或修改了任何文件。
"""
import os
import time
import datetime

ROOT = r"D:\yaorz\research"
SKIP_DIRS = {"models", ".git", "node_modules", "hf_cache", "__pycache__", "outputs", ".venv_funprm"}
SINCE = time.mktime(time.strptime("2026-09-28 13:35:00", "%Y-%m-%d %H:%M:%S"))

print("now =", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("threshold = 2026-09-28 13:35:00")

hits = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in filenames:
        path = os.path.join(dirpath, name)
        try:
            st = os.stat(path)
        except OSError:
            continue
        if st.st_mtime > SINCE:
            hits.append((st.st_mtime, st.st_size, os.path.relpath(path, ROOT)))

hits.sort()
print("\n--- files modified after threshold: %d ---" % len(hits))
for mtime, size, rel in hits:
    print("  %s  %10d  %s" % (time.strftime("%H:%M:%S", time.localtime(mtime)), size, rel))

print("\n--- repo root listing (suspicious new entries) ---")
for name in sorted(os.listdir(ROOT)):
    path = os.path.join(ROOT, name)
    st = os.stat(path)
    flag = ""
    if st.st_mtime > SINCE:
        flag = "  <== recently touched"
    kind = "DIR " if os.path.isdir(path) else "FILE"
    print("  %s  %s%s" % (kind, name, flag))
