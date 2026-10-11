# P5 数据门状态：2026-09-17

此前的“缺少 medium/hard 数据”阻塞已解除。通过项目内的标准抓取脚本取得并审计了 APPS train 的 Interview 难度 30 行：

- `data/raw/apps_train_interview30.json`：30 行，包含 25 道函数题和 5 道 stdin/stdout 题；
- `data/raw/apps_train_interview_function25.json`：从上述 30 行中按 `execution_mode=function` 预先筛出的 25 道函数题；
- 原始数据的 public/private 测试均存在，未发现空测试集；
- 原始数据哈希和筛选规则记录于 `experiments/decomprl_20260914/manifest.json`。

模块化协议要求可调用 starter API，因此 5 道 stdin/stdout 题在看到任何实验结果前就排除；M0/M1 的 30 行正式结果在分析时过滤到同一 25 行，保证比较分母一致。P5 正式报告见 `reports/p5_interview_function25_analysis_20260917.md`。

当前结论仍然是：不启动 RL 训练。P5 的作用是检验更难数据上的机制稳定性，而不是替代官方 APPS 测试集或声称复现论文训练规模。
