"""WP3 遗留项：可拆分性五项判据的双标注一致率计算（标注员 A vs B）。

要求（执行文档 §8.2 第 7 条）：至少两名独立标注者或两个独立 Agent；报告逐项原始一致数、一致率与全部分歧。
若计算 Cohen's kappa，必须同时报告原始一致数（本项目不把 kappa 当唯一指标）。
"""
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(r"D:\yaorz\research\decomposition-bench")
ANN = ROOT / "experiments/wp3_classeval/annotation"
OUT = ANN / "agreement.json"
CRITERIA = ["多阶段", "接口清楚", "可独立验证", "测试能区分", "非单一洞察"]


def kappa(pairs):
    """pairs: [(a,b)] 三分类；返回 (kappa, po, pe)，样本为空时返回 None。"""
    n = len(pairs)
    if n == 0:
        return None
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    k = (po - pe) / (1 - pe) if pe < 1 else None
    return k, po, pe


def main() -> None:
    a = json.loads((ANN / "annotator_A.json").read_text(encoding="utf-8"))
    b = json.loads((ANN / "annotator_B.json").read_text(encoding="utf-8"))
    A = {t["task_id"]: t["judgments"] for t in a["tasks"]}
    B = {t["task_id"]: t["judgments"] for t in b["tasks"]}
    shared = sorted(set(A) & set(B), key=lambda t: int(t.split("_")[-1]))

    report = {"annotator_A_tasks": len(A), "annotator_B_tasks": len(B), "shared_tasks": len(shared),
              "only_A": sorted(set(A) - set(B)), "only_B": sorted(set(B) - set(A)), "per_criterion": {}, "disagreements": []}
    all_pairs = []
    for c in CRITERIA:
        pairs = [(A[t][c], B[t][c]) for t in shared]
        all_pairs += pairs
        k = kappa(pairs)
        agree = sum(1 for x, y in pairs if x == y)
        report["per_criterion"][c] = {
            "n": len(pairs), "raw_agree": agree, "agree_rate": round(agree / len(pairs), 3),
            "cohen_kappa": round(k[0], 3) if k and k[0] is not None else None,
            "A_dist": dict(Counter(A[t][c] for t in shared)), "B_dist": dict(Counter(B[t][c] for t in shared)),
        }
    for t in shared:
        for c in CRITERIA:
            if A[t][c] != B[t][c]:
                report["disagreements"].append({"task_id": t, "criterion": c, "A": A[t][c], "B": B[t][c]})
    k_all = kappa(all_pairs)
    report["overall"] = {"n": len(all_pairs), "raw_agree": sum(1 for x, y in all_pairs if x == y),
                         "agree_rate": round(sum(1 for x, y in all_pairs if x == y) / len(all_pairs), 3),
                         "cohen_kappa": round(k_all[0], 3) if k_all and k_all[0] is not None else None}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("共享题数:", len(shared), "| A 独有:", report["only_A"])
    print(f"总体：原始一致 {report['overall']['raw_agree']}/{report['overall']['n']}"
          f" = {report['overall']['agree_rate']:.3f}，kappa={report['overall']['cohen_kappa']}")
    for c in CRITERIA:
        d = report["per_criterion"][c]
        print(f"  {c}: {d['raw_agree']}/{d['n']} = {d['agree_rate']:.3f} kappa={d['cohen_kappa']} | A={d['A_dist']} B={d['B_dist']}")
    print("分歧数:", len(report["disagreements"]))
    print("产物:", OUT)


if __name__ == "__main__":
    main()
