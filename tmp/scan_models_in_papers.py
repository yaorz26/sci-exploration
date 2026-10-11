"""统计本项目已在本地抽取文本的论文里，各自使用了哪些模型、以及给出的理由。

用于回答用户问题："相关论文研究都用的是什么模型、为什么用这些、为什么不用更强的模型"。
只做检索与计数，不改任何文件。证据来源：archive/pdftext/*.txt（PDF 抽取文本）。
"""
import collections
import pathlib
import re

TEXTDIR = pathlib.Path(r"D:\yaorz\research\archive\pdftext")

MODELS = [
    "GPT-4o-mini", "GPT-4o", "GPT-4-Turbo", "GPT-4", "GPT-3.5", "o1-mini", "o1", "o3",
    "Claude-3", "Claude 3", "Claude", "Gemini",
    "DeepSeek-R1", "DeepSeek-V3", "DeepSeek-Coder", "DeepSeek",
    "Qwen2.5-Coder", "Qwen2.5", "Qwen",
    "CodeLlama", "Llama-3", "Llama 3", "Llama-2", "Llama 2", "Llama",
    "StarCoder2", "StarCoder 2", "StarCoder", "CodeGen", "WizardCoder", "Mistral", "Phi-3", "Phi",
    "code-davinci", "text-davinci", "PaLM", "CodeT5", "Gemma",
]
REASONS = {
    "开源/可复现": r"open[- ]?source|reproducib|open weights|publicly available",
    "成本/预算": r"\bcost\b|budget|expensive|cheaper|price",
    "上下文长度": r"context (?:window|length)|long[- ]context|128K|token limit",
    "训练需求": r"\bRL\b|reinforcement learning|fine[- ]?tun|instruction tun",
    "API 不可控/漂移": r"API|closed[- ]?source|proprietary",
    "硬件/显存": r"\bGPU\b|H100|A100|VRAM|memory",
}


def main() -> None:
    print(f"{'论文':38s}" + "".join(f"{m:>13s}" for m in ["模型总提及", "主要模型(前3)"]))
    print("-" * 100)
    for p in sorted(TEXTDIR.glob("*.txt")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        counts = {m: len(re.findall(re.escape(m), txt)) for m in MODELS}
        hits = {m: c for m, c in counts.items() if c > 0}
        top = sorted(hits.items(), key=lambda kv: -kv[1])[:5]
        print(f"{p.stem[:38]:38s}{sum(hits.values()):>13d}   {top}")
    print()
    print('=== 各文件里"用开源/成本/规模"相关理由的句子（各取 2 条） ===')
    for p in sorted(TEXTDIR.glob("*.txt")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        print(f"\n--- {p.stem} ---")
        for label, pat in REASONS.items():
            for m in list(re.finditer(pat, txt, re.I))[:2]:
                s = max(0, m.start() - 110)
                frag = " ".join(txt[s:m.start() + 150].split())
                print(f"  [{label}] …{frag}…")


if __name__ == "__main__":
    main()
