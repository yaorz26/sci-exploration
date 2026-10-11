"""最多两次单token校准：核对原生分词、显式raw模板和Ollama默认模板。"""
import json
import urllib.request
from pathlib import Path

from budgeted_generation import BudgetedClient
from native_tokenizer import NativeTokenizer, render_chatml


def main():
    root = Path(__file__).resolve().parents[2]
    out = root / "experiments/d1_tokenizer_integration_v1_20261008"
    config = json.loads((out / "calibration_contract.json").read_text(encoding="utf-8"))
    tokenizer = NativeTokenizer(config["model_path"], config["library_directory"])
    def transport(body):
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    client = BudgetedClient(out / "calibration", config["total_token_limit"], 2, transport)
    prompt = config["prompt"]
    expected = tokenizer.count(render_chatml(prompt))
    checks = []
    try:
        for raw in (True, False):
            actual_prompt = render_chatml(prompt) if raw else prompt
            client.request(actual_prompt, config["model"], {"temperature": 0, "seed": config["seed"], "num_ctx": 8192},
                           expected, 1, "explicit_raw" if raw else "default_template", raw=raw, context_limit=8192)
            measured = client.calls[-1]["prompt_tokens"]
            checks.append({"raw": raw, "native_expected": expected, "api_measured": measured, "match": measured == expected})
            if measured != expected:
                break
    finally:
        tokenizer.close()
        report = {"checks": checks, "real_model_calls": len(client.calls), "known_token_spend": client.spent,
                  "status": "pass" if len(checks) == 2 and all(row["match"] for row in checks) else "revise",
                  "scope": "非任务混合文本和模板的两个单token实测，不证明所有端点/配置等价；模型身份与显式raw渲染冻结后再用"}
        (out / "calibration_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
