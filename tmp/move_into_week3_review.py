"""把 计划审核中 目录内的全部文件移入 docs/week3/计划审核，并删除空目录。

- 源：D:\\yaorz\\research\\计划审核中
- 目标：D:\\yaorz\\research\\docs\\week3\\计划审核（已存在且为空，允许写入；若已有同名文件则中止）
- 移动前后逐一比对 SHA-256。
"""
import hashlib
import os
import shutil

SRC = r"D:\yaorz\research\计划审核中"
DST = r"D:\yaorz\research\docs\week3\计划审核"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


if not os.path.isdir(SRC):
    raise SystemExit("ABORT: source missing -> %s" % SRC)
if not os.path.isdir(DST):
    raise SystemExit("ABORT: target directory missing -> %s" % DST)

names = sorted(n for n in os.listdir(SRC) if os.path.isfile(os.path.join(SRC, n)))
for name in names:
    if os.path.exists(os.path.join(DST, name)):
        raise SystemExit("ABORT: target file exists -> %s" % os.path.join(DST, name))

print("--- before ---")
before = {}
for name in names:
    path = os.path.join(SRC, name)
    before[name] = sha256(path)
    print("  %9d  %s" % (os.path.getsize(path), name))

for name in names:
    shutil.move(os.path.join(SRC, name), os.path.join(DST, name))
    print("moved: %s" % name)

print("\n--- hash verification ---")
ok = True
for name in names:
    after = sha256(os.path.join(DST, name))
    same = after == before[name]
    ok = ok and same
    print("  %s  %s" % ("OK  " if same else "DIFF", name))
print("all identical:", ok)

left = os.listdir(SRC)
print("\nleftovers in source:", left)
if not left:
    os.rmdir(SRC)
    print("removed empty source dir:", SRC)

print("\n--- workspace root ---")
for name in sorted(os.listdir(r"D:\yaorz\research")):
    path = os.path.join(r"D:\yaorz\research", name)
    print("  %s  %s" % ("DIR " if os.path.isdir(path) else "FILE", name))

print("\n--- docs/week3/计划审核 ---")
for name in sorted(os.listdir(DST)):
    path = os.path.join(DST, name)
    print("  %9d  %s  %s" % (os.path.getsize(path), sha256(path)[:16], name))
