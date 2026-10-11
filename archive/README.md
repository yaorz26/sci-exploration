# archive/ 说明

创建时间：2026-09-18（项目整理）

本目录存放**无文档引用、可再生成**的中间产物，从 `tmp/` 和 `.tmp/` 移入。移入前已确认：

- `docs/`、`codeprm-reproduction/reports/`、`codeprm-reproduction/scripts/`、`src/`、`configs/` 中均无对这些路径的引用（2026-09-18 grep 核查）。

## 内容清单

| 条目 | 原位置 | 是什么 | 如何再生 |
| --- | --- | --- | --- |
| `pdfs/` | `tmp/pdfs/` | 各论文阅读时的 PDF 逐页截图（APPS/DecompRL/FunPRM/CodePRM 等） | 用 PDF 阅读工具重新渲染 `articles/` 下对应 PDF |
| `pdftext/` | `tmp/pdftext/` | 论文 PDF 的纯文本抽取：`2025.findings-acl.428` = CodePRM、`2601.22249` = FunPRM、AdapTrack、EfficientGrammer-Constrained、Lookahead-then-Verify、SeeCodePRM；**2026-09-26 新增** `08_DecompRL.txt`（29 页）与 `09_MoT.txt`（22 页） | 对 `articles/` 下同名 PDF 重新抽取文本（脚本：`tmp/extract_extra_pdfs.py`） |
| `decomprl-source.tar` | `tmp/decomprl-source.tar` | DecompRL 论文的 arXiv 源码包（LaTeX） | 从 arXiv 重新下载该论文 source |
| `pdf-summary/` | `.tmp/pdf-summary/` | FunPRM / CodePRM 部分页面的渲染图（某次 PDF 总结会话的临时产物） | 重新渲染对应页面 |

## 约定

- 本目录内容**不参与**任何实验结论与报告引用，可安全删除；
- 保留它们只为省去将来重新下载/渲染的成本；
- 若磁盘紧张，优先删除 `pdfs/` 和 `pdf-summary/`（纯图片，信息完全包含在 PDF 原文中）。

## 例外记录（2026-09-26）

`pdftext/08_DecompRL.txt` 与 `pdftext/09_MoT.txt` 是 2026-09-26 新增的原文文本抽取，被
`docs/week2/阶段一拆解机制负结果深度归因与论文拆分对照_20260926.md` **引用为原文核对依据**（DecompRL 的
Table 1 预算曲线、Table 4 无 RL 结果、§2.1 条件独立假设、§6 格式税与规模坍缩；MoT 的 Algorithm 1）。
因此这两个文件在引用期内不属于"可安全删除"范围；如需清理，请先确认上述文档已不再需要复核。
`pdfs/`、`pdf-summary/` 与其余 pdftext 文件仍按原约定处理。
