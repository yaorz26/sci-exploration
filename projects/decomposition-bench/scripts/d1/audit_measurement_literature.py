"""P39定向文献记录：仅核对已缓存官方v1文本，不获取新版本。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_measurement_contribution_literature_v1_20261008"
CACHE = ROOT / "experiments/d1_literature_fulltext_v1_20261008"

SEGMENTS = [
    ("2503.06680", "FEA-Bench", "表2/4.2", 336, 340,
     "单轮生成；BM25提示27K、生成4K用于32K上下文；该单轮联合限制不能直接等同跨阶段、预检和重试的题—方法总上限。"),
    ("2503.06680", "FEA-Bench", "附录B.2", 1748, 1764,
     "每题一次生成；部分模型输出上限4096，另有8192、100000、65536。不能将表2的4K推广给全部配置。"),
    ("2602.10975", "FeatureBench", "3.1—3.2新问题定向回查", 142, 156,
     "报告Resolved/Passed/输入输出Token IO；动态函数调用依赖图用于原仓库任务抽取，不是生成后方案返回值贡献测量。"),
    ("2602.10975", "FeatureBench", "4.1.1", 230, 236,
     "默认每题最多500步，另报告消耗token；在本段未发现把各方法预检/重试/输入输出统一控制在相同题级token cap的设计。"),
    ("2602.10975", "FeatureBench", "4.1.3", 363, 370,
     "用NameError/TypeError/AttributeError/AssertionError分析失败；本段未给合法拒绝、作为数据的错误标记、局部投影缺值及无候选占位的联合分母。"),
    ("2602.10975", "FeatureBench", "4.2.2", 459, 465,
     "提供真实单元测试和增加最大执行步数是消融因素；步骤限制不是同总token限制，测试可见消融不适用于D1既定private隔离。"),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    dest = OUT / "targeted_evidence_and_contribution_review.json"
    if dest.exists():
        raise FileExistsError("旧机器证据不得覆盖")
    access = json.loads((CACHE / "access_record.json").read_text(encoding="utf-8"))
    records = []
    sources = []
    for old in access:
        sid = old["id"]
        html = CACHE / (sid + ".html")
        if digest(html) != old["sha256"]:
            raise ValueError("官方缓存哈希变化，停止引用旧定位")
        sources.append({"id": sid, "url": old["url"], "html_sha256": old["sha256"],
                        "text_sha256": digest(CACHE / (sid + ".txt")),
                        "access_mode": "此前官方v1缓存，本阶段未成功联网获取，不核实当前最新版"})
    for sid, title, section, lo, hi, conclusion in SEGMENTS:
        lines = (CACHE / (sid + ".txt")).read_text(encoding="utf-8").splitlines()
        window = "\n".join(lines[lo-1:hi])
        if len(lines[lo-1:hi]) != hi-lo+1:
            raise ValueError("定位越界")
        records.append({"source_id": sid, "title": title, "section": section,
                        "text_lines": [lo, hi], "window_sha256": hashlib.sha256(window.encode()).hexdigest(),
                        "paraphrase": conclusion, "verbatim_quote_words": 0})
    review = {
        "status": "定向核对完成，候选贡献收窄；非穷尽新颖性检索",
        "created_at": datetime.now(timezone.utc).isoformat(), "sources": sources, "segments": records,
        "comparison": [
            {"dimension": "功能级题/明确接口/执行测试", "covered": "两篇已覆盖", "D1_claim": "不作为首创；D1为轻量库适配而非等同完整仓库任务"},
            {"dimension": "输入输出token", "covered": "FeatureBench明确Token IO；FEA单轮有上下文与不同输出cap", "D1_claim": "不作为首创；比较的是相同题—方法总cap及所有阶段计费，不保证唯一改变分解"},
            {"dimension": "任务结构与生成后计划", "covered": "FeatureBench任务抽取依赖图", "D1_claim": "所查段落未给同预算结构关联及生成后状态所有权/返回贡献的联合测量；不能声称所有文献均无"},
            {"dimension": "失败与观察分母", "covered": "FeatureBench异常类型/整题与部分通过", "D1_claim": "所查段落未给D1几类观察域边界的联合口径；反例是候选测量诊断而非新测试理论"},
        ],
        "competing_explanations": {
            "已有工作完整覆盖D1拟测框架": "在限定六段中未获支持，不能据此作全领域不存在断言",
            "已有工作覆盖组成部分但联合设计仍需验证": "获支持，必须引用已有贡献并收窄D1表述",
            "D1现有证据不足以证明A或稳定新测量": "保留；人工0、同总cap完整M2不足，手工反例不能补模型关联"
        },
        "decision": "停止扩同类反例与文献；P40先查原20任务在既定切分/来源/相关组件下能支持哪些前置结构比较，再决定问题驱动补足。",
        "budgets": {"source_count": 2, "relevant_segments": 6, "model_calls": 0, "API_calls": 0,
                    "new_paper_downloads": 0, "hidden_reads": 0, "task_evaluations": 0},
        "limits": ["只核对固定v1缓存和指定段落，不是全文通读/最新版本/穷尽检索", "原始web通道失败保留，不重试不支持通道", "不声称新型关系测试、动态依赖或动态切片首创", "数据集/诊断可为成果，结构收益关联仍未验证"]
    }
    dest.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": review["status"], "sources": 2, "segments": 6, "model_calls": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
