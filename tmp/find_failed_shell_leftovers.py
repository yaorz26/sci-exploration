"""定位失败命令留下的副产物（只读，不删除）。

第一条审计脚本的阈值写成了 13:35:00，晚于执行时刻 13:34:31，因此命中数为 0，
结果无效。本脚本改用 13:28:30 作为阈值（晚于 13:27:28 的正常记忆写入），
列出工作区内被修改的文件，并对根目录下的可疑文件输出内容预览。
"""
import os
import time

ROOT = r"D:\yaorz\research"
SKIP_DIRS = {"models", ".git", "node_modules", "hf_cache", "__pycache__", "outputs", ".venv_funprm"}
SINCE = time.mktime(time.strptime("2026-09-28 13:28:30", "%Y-%m-%d %H:%M:%S"))

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
            hits.append((st.st_mtime, st.st_size, path))

hits.sort()
print("threshold = 2026-09-28 13:28:30")
print("--- all files modified after threshold: %d ---" % len(hits))
for mtime, size, path in hits:
    print("  %s  %9d  %s" % (time.strftime("%H:%M:%S", time.localtime(mtime)), size, os.path.relpath(path, ROOT)))

print("\n--- preview of every file directly in repo root ---")
for name in sorted(os.listdir(ROOT)):
    path = os.path.join(ROOT, name)
    if os.path.isdir(path):
        continue
    st = os.stat(path)
    marker = "RECENT" if st.st_mtime > SINCE else "      "
    print("\n[%s] %s  (size=%d, mtime=%s)" % (
        marker, name, st.st_size, time.strftime("%H:%M:%S", time.localtime(st.st_mtime))))
    if st.st_size < 4096:
        try:
            text = open(path, encoding="utf-8").read()
        except Exception as exc:  # noqa: BLE001
            text = "<unreadable: %s>" % exc
        print("    content: %r" % text[:200])
