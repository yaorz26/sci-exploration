"""检查 docs/week3 与 docs/week3/计划审核 的当前状态。"""
import hashlib
import os
import time

W3 = r"D:\yaorz\research\docs\week3"
REVIEW = os.path.join(W3, "计划审核")
ROOT_FOLDER = r"D:\yaorz\research\计划审核中"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def show(directory):
    print("\n[%s] exists=%s" % (directory, os.path.isdir(directory)))
    if not os.path.isdir(directory):
        return
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if os.path.isdir(path):
            print("  DIR   %s" % name)
        else:
            st = os.stat(path)
            print("  %6d  %s  %s" % (st.st_size, time.strftime("%H:%M:%S", time.localtime(st.st_mtime)), name))


show(W3)
show(REVIEW)
show(ROOT_FOLDER)

print("\n--- recursive listing of docs/week3 ---")
for dirpath, dirnames, filenames in os.walk(W3):
    for name in sorted(filenames):
        path = os.path.join(dirpath, name)
        st = os.stat(path)
        print("  %s  %8d  %s  %s" % (
            time.strftime("%H:%M:%S", time.localtime(st.st_mtime)),
            st.st_size,
            os.path.relpath(path, W3),
            sha256(path)[:16],
        ))
