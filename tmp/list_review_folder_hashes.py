"""打印 计划审核中 目录内文件的名称、大小与 SHA-256（用于写入目录说明）。"""
import hashlib
import os

DST = r"D:\yaorz\research\计划审核中"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


for name in sorted(os.listdir(DST)):
    path = os.path.join(DST, name)
    if not os.path.isfile(path):
        continue
    print("%s | %d | %s" % (name, os.path.getsize(path), sha256(path)))

print()
kept = r"D:\yaorz\research\docs\week3\9.28数据集路线_分步执行与Agent移交文档.md"
print("KEPT | %s | %d | %s" % (os.path.basename(kept), os.path.getsize(kept), sha256(kept)))
