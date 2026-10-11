"""把 docs/week3 中除"修订后最终结果"以外的文件移入 计划审核中。

规则：
- 保留：docs/week3/9.28数据集路线_分步执行与Agent移交文档.md （修订后最终结果 = v3）
- 移入 D:\\yaorz\\research\\计划审核中\\ ：其余 6 个文件
- 不改动任何被移动文件的内容；移动前后逐一比对 SHA-256，必须完全一致。
- 目标已存在同名文件则中止，不做覆盖。

先打印清单与哈希，再执行移动，最后复核两个目录。
"""
import hashlib
import os
import shutil

SRC = r"D:\yaorz\research\docs\week3"
DST = r"D:\yaorz\research\计划审核中"
KEEP = {"9.28数据集路线_分步执行与Agent移交文档.md"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def listing(directory):
    if not os.path.isdir(directory):
        return []
    return sorted(
        (name, os.path.getsize(os.path.join(directory, name)))
        for name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, name))
    )


print("--- BEFORE ---")
for label, directory in (("src", SRC), ("dst", DST)):
    print("[%s] %s" % (label, directory))
    for name, size in listing(directory):
        print("    %9d  %s" % (size, name))

moves = [(name, size) for name, size in listing(SRC) if name not in KEEP]
print("\n--- planned moves (%d) ---" % len(moves))
for name, size in moves:
    print("    %9d  %s" % (size, name))

os.makedirs(DST, exist_ok=True)

for name, _ in moves:
    target = os.path.join(DST, name)
    if os.path.exists(target):
        raise SystemExit("ABORT: target already exists -> %s" % target)

before = {name: sha256(os.path.join(SRC, name)) for name, _ in moves}

for name, _ in moves:
    shutil.move(os.path.join(SRC, name), os.path.join(DST, name))
    print("moved: %s" % name)

print("\n--- hash verification ---")
ok = True
for name, digest in sorted(before.items()):
    after = sha256(os.path.join(DST, name))
    same = after == digest
    ok = ok and same
    print("  %s  %s" % ("OK  " if same else "DIFF", name))
    if not same:
        print("       before=%s\n       after =%s" % (digest, after))
print("all identical:", ok)

print("\n--- AFTER ---")
for label, directory in (("src", SRC), ("dst", DST)):
    print("[%s] %s" % (label, directory))
    for name, size in listing(directory):
        print("    %9d  %s" % (size, name))
