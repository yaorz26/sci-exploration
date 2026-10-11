"""列出 2026-09-28 13:40 之后被修改的所有文件，用于确认是否出现新的修订产物。"""
import os
import time

ROOT = r"D:\yaorz\research"
SKIP_DIRS = {"models", ".git", "node_modules", "hf_cache", "__pycache__", "outputs", ".venv_funprm", ".pytest_cache"}
SINCE = time.mktime(time.strptime("2026-09-28 13:40:00", "%Y-%m-%d %H:%M:%S"))

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
print("threshold = 2026-09-28 13:40:00")
print("--- %d file(s) modified after threshold ---" % len(hits))
for mtime, size, rel in hits:
    print("  %s  %9d  %s" % (time.strftime("%H:%M:%S", time.localtime(mtime)), size, rel))

print("\n--- docs tree ---")
for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "docs")):
    rel = os.path.relpath(dirpath, ROOT)
    for name in sorted(filenames):
        path = os.path.join(dirpath, name)
        st = os.stat(path)
        print("  %s  %8d  %s" % (time.strftime("%H:%M", time.localtime(st.st_mtime)), st.st_size, os.path.join(rel, name)))

print("\n--- workspace root ---")
for name in sorted(os.listdir(ROOT)):
    path = os.path.join(ROOT, name)
    kind = "DIR " if os.path.isdir(path) else "FILE"
    print("  %s  %s" % (kind, name))
