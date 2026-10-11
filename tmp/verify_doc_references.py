"""校验正式结果文档中所有 `docs/...` 路径引用是否真实存在。"""
import os
import re

ROOT = r"D:\yaorz\research"
DOC = os.path.join(ROOT, "docs", "week3", "9.28数据集路线_分步执行与Agent移交文档.md")

text = open(DOC, encoding="utf-8").read()
refs = sorted(set(re.findall(r"docs/[^\s`）)，,、]+\.(?:md|json|csv|py)", text)))

print("文档：%s" % DOC)
print("扫描到的 docs/ 引用：%d 个\n" % len(refs))
missing = 0
for ref in refs:
    target = os.path.join(ROOT, ref.replace("/", os.sep))
    ok = os.path.exists(target)
    if not ok:
        missing += 1
    print("  %s  %s" % ("OK     " if ok else "MISSING", ref))
print("\n缺失数：%d" % missing)
