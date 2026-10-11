# 严格预检运行索引

运行器：`run_pair.py`；本地 tokenizer：`codeprm-reproduction/models/Qwen2.5-Coder-7B-Instruct/tokenizer.json`。

每个请求先把 ChatML 输入计数与剩余每臂 6500 token 对照，再设置 `num_predict`；若最小请求超出，保存 `preflight.json` 并不发送。服务端 `prompt_eval_count` 与本地预检逐次相等。

- PR126 M0：3812+1600=5412，严格 hunk 失败。
- PR126 M2：计划 4114+300=4414，计划 JSON 解析失败。
- PR142 M0：3978+1477=5455，严格 hunk 失败。
- PR142 M2：计划 4452+136=4588；组件预检剩余 -2028，拒绝发送。

四臂均无完整候选，未运行行为评价。
