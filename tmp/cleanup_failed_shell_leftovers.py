"""清理 2026-09-28 13:34 由失败 shell 命令误创建的空文件。

安全约束（硬编码，不依赖通配符）：
- 只处理「仓库根目录直属文件」；
- 只处理 size == 0；
- 只处理 mtime 落在 13:33:50 -- 13:34:10 之间；
- 名称不含已知合法文件白名单中的任何一项。

先打印将删除的清单与理由，再删除，然后复核根目录。
"""
import os
import time

ROOT = r"D:\yaorz\research"
LO = time.mktime(time.strptime("2026-09-28 13:33:50", "%Y-%m-%d %H:%M:%S"))
HI = time.mktime(time.strptime("2026-09-28 13:34:10", "%Y-%m-%d %H:%M:%S"))
ALLOW = {".gitignore", "AGENTS.md", "README.md", "PROJECT_MEMORY.md", "当前情况总结.md"}

targets = []
for name in sorted(os.listdir(ROOT)):
    path = os.path.join(ROOT, name)
    if os.path.isdir(path):
        continue
    st = os.stat(path)
    if name in ALLOW:
        continue
    if st.st_size != 0:
        continue
    if not (LO <= st.st_mtime <= HI):
        continue
    targets.append((path, st.st_mtime))

print("--- candidates (%d) ---" % len(targets))
for path, mtime in targets:
    print("  %s  size=0  mtime=%s" % (path, time.strftime("%H:%M:%S", time.localtime(mtime))))

print("\n--- deleting ---")
for path, _ in targets:
    os.remove(path)
    print("  removed: %s" % path)

print("\n--- repo root after cleanup ---")
for name in sorted(os.listdir(ROOT)):
    path = os.path.join(ROOT, name)
    kind = "DIR " if os.path.isdir(path) else "FILE"
    print("  %s  %s" % (kind, name))
