"""把误放在工作区根的 计划审核中 目录整体移入 docs/week3/计划审核。

- 目标：D:\\yaorz\\research\\docs\\week3\\计划审核\\
- 源：  D:\\yaorz\\research\\计划审核中\\
- 移动前后逐一比对每个文件的 SHA-256，必须完全一致。
- 目标存在则中止；移动后若源目录为空则删除该空目录。
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
if os.path.exists(DST):
    raise SystemExit("ABORT: target already exists -> %s" % DST)

names = sorted(n for n in os.listdir(SRC) if os.path.isfile(os.path.join(SRC, n)))
print("--- before ---")
before = {}
for name in names:
    path = os.path.join(SRC, name)
    before[name] = sha256(path)
    print("  %9d  %s" % (os.path.getsize(path), name))

os.makedirs(DST, exist_ok=True)
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

leftovers = os.listdir(SRC)
print("\nleftovers in source:", leftovers)
if not leftovers:
    os.rmdir(SRC)
    print("removed empty source dir:", SRC)

print("\n--- docs/week3 ---")
parent = r"D:\yaorz\research\docs\week3"
for name in sorted(os.listdir(parent)):
    path = os.path.join(parent, name)
    kind = "DIR " if os.path.isdir(path) else "FILE"
    print("  %s  %s" % (kind, name))

print("\n--- docs/week3/计划审核 ---")
for name in sorted(os.listdir(DST)):
    path = os.path.join(DST, name)
    print("  %9d  %s" % (os.path.getsize(path), name))
