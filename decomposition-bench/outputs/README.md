# 输出目录说明

`outputs/` 是运行产物，不是研究结论入口。正式数字应同步到 `reports/` 和 `.research-state/`，并保留机器结果路径。

- `executions/`：程序执行记录。
- `generations/`：模型生成原文。
- `results/`：选择结果和汇总。
- `models/`：训练后的 adapter 或其他模型产物。
- `neural_pilot/`：早期神经实验产物，默认不纳入 Git。

不要手动删除或覆盖输出；需要新配置时使用新输出目录或后缀。
