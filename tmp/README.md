# tmp/ 说明（重要：本目录脚本不可移动或重命名）

`tmp/` 存放**分析/审计脚本**。它们虽然名字像临时文件，但被 `docs/week1/` 多份文档引用为**可复核证据**（引用处记录了脚本路径与复核结论），因此：

1. **不要移动、不要重命名**这些脚本——会破坏文档中的引用链；
2. **不要删除**——它们是 week1 阶段各结论的复算入口。

## 脚本清单与引用关系（2026-09-18 核查）

| 脚本 | 作用 | 被引用于 |
| --- | --- | --- |
| `observation_stats.py` | 粒度统计与 public/private 一致性（Spearman 0.825、单函数 183/200 等关键数字的来源） | `科研执行清单.md`、`阶段4_研究假设一页纸.md`、`debate/` |
| `build_observation_material_v2.py` | 生成 `阶段2_手工观察素材.md` 的素材构建脚本 | `科研执行清单.md`、`debate/` |
| `audit_debate_claims.py` / `audit_debate_supplement.py` / `audit_tiebreak_rules.py` | 对反驳文档与同分规则争议的复核脚本 | `debate/审查_对反驳文档的复核.md`、`研究方向_第二轮_从对话记录提取.md` |
| `failure_taxonomy.py` | 失败分类统计 | `研究方向_第二轮_从对话记录提取.md` |
| `build_observation_material.py` | v1 版素材脚本（已被 v2 取代，保留作历史） | — |
| `check_split.py` / `select_problems.py` / `inspect_records.py` / `reproduce_baselines.py` | 数据检查、选题与记录检查的辅助脚本 | — |

## 历史备注

2026-09-18 整理时，本目录原有的 PDF 截图（`pdfs/`）、纯文本抽取（`pdftext/`）和论文源码包（`decomprl-source.tar`）因无任何引用已移至 `archive/`。
