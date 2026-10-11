"""一次性工具：把 extra 目录的 PDF 抽取为纯文本，补齐 archive/pdftext/。

用途：核对论文原文关键表述（尤其是 DecompRL 的无 RL 层级结果、条件独立假设、
预算曲线等），避免只依赖二手整理。输出与 archive/pdftext/ 既有命名一致。
"""

from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(r"D:\yaorz\research")
SRC_DIR = ROOT / "articles" / "extra"
OUT_DIR = ROOT / "archive" / "pdftext"

TARGETS = {
    "08_DecompRL_Solving_Harder_Problems_by_Learning_Modular_Code_Generation.pdf": "08_DecompRL.txt",
    "09_MoT.pdf": "09_MoT.txt",
}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src_name, out_name in TARGETS.items():
        src = SRC_DIR / src_name
        if not src.exists():
            print(f"[skip] 源文件不存在：{src}")
            continue
        reader = PdfReader(str(src))
        chunks: list[str] = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                text = f"[extract_error page {i}: {exc}]"
            chunks.append(f"\n===== PAGE {i} =====\n{text}")
        out = OUT_DIR / out_name
        out.write_text("".join(chunks), encoding="utf-8")
        print(f"[ok] {src.name} -> {out.name}，{len(reader.pages)} 页，{out.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
