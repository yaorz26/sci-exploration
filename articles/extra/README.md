# AI 代码生成：补充论文阅读包

下载日期：2026-09-10  
阅读目标：服务于当前的研究问题——**在不泄漏 private 测试的前提下，执行反馈与过程信息能否更可靠地选择或修正代码候选**。

本目录按推荐阅读顺序保存七份原始 PDF 和七份中文总结。PDF 是原文依据；总结刻意加入了“它没有证明什么”和“与当前实验的关系”，避免把作者的结论直接搬到不等价的小规模 APPS 设置中。

| 顺序 | 论文 | 原始 PDF | 中文总结 | 为什么排在这里 |
| --- | --- | --- | --- | --- |
| 1 | ReCode | [PDF](01_ReCode_Reasoning_Process_Rewards.pdf) | [总结](01_ReCode_中文总结.md) | 过程奖励如何进入训练，以及如何防止模型只迎合奖励而不把程序做对。 |
| 2 | LEVER | [PDF](02_LEVER_Learning_to_Verify_with_Execution.pdf) | [总结](02_LEVER_中文总结.md) | 最接近当前候选重排序：从“题目 + 代码 + 执行结果”学习验证器。 |
| 3 | CodeT | [PDF](03_CodeT_Code_Generation_with_Generated_Tests.pdf) | [总结](03_CodeT_中文总结.md) | 没有足够测试时，怎样生成测试并选择多个候选。 |
| 4 | DiffCodeGen | [PDF](04_DiffCodeGen_Differential_Test_Time_Scaling.pdf) | [总结](04_DiffCodeGen_中文总结.md) | 不使用已有公开测试，通过差分行为挑选候选；是直接竞争基线。 |
| 5 | Reason-Code | [PDF](05_Reason_Code_Test_Driven_MCTS.pdf) | [总结](05_Reason_Code_中文总结.md) | 在低预算下把执行反馈用于“失败后才搜索”的修正流程。 |
| 6 | Revisit Self-Debugging | [PDF](06_Revisit_Self_Debugging_with_Self_Generated_Tests.pdf) | [总结](06_Revisit_Self_Debugging_中文总结.md) | 解释自生成测试为何会误导修正，直接约束当前实验的解释。 |
| 7 | EvalPlus | [PDF](07_EvalPlus_Rigorous_Code_Generation_Evaluation.pdf) | [总结](07_EvalPlus_中文总结.md) | 检查最终评价测试是否足以支持“功能正确”的结论。 |

## 建议的读法

第一轮只读每份总结中的“问题、方法、结论、与当前工作的关系”，并在纸上写下每篇的一句话。第二轮再看 PDF 的图 1、方法小节和实验设置。不要一开始就被公式、模型名称或大量表格拖慢。

这七篇合起来回答的是不同层次的问题：

```text
过程信号能否训练模型？             ReCode
        ↓
执行结果能否帮我挑候选？           LEVER / CodeT / DiffCodeGen
        ↓
执行反馈能否在失败后指导搜索？     Reason-Code
        ↓
自造测试会不会把我带偏？           Revisit Self-Debugging
        ↓
最终“正确”这一评价本身可靠吗？    EvalPlus
```

## 贯穿所有论文的实验红线

1. **选择阶段只能使用可见信息。** public 测试、模型自己生成的测试、执行轨迹都可以是方法输入；private 测试不能进入 prompt、重排序或阈值调参。
2. **通过少量样例不等于正确。** 它至多说明“通过这些样例”；必须用独立且更充分的 private 测试给最后结论。
3. **候选一致不等于候选正确。** CodeT 和 DiffCodeGen 都借用“多数行为更可信”的假设；当模型系统性误解题意时，错误答案也可能形成多数。
4. **不要把训练结果与推理时选择混为一谈。** ReCode 是训练生成器的工作；LEVER、CodeT、DiffCodeGen 更接近当前的测试时选择问题。
5. **比较时冻结候选池和预算。** 若一组方法额外生成候选、额外调用大模型或额外查看测试，必须在报告中单列该成本，不能只比较最终 pass rate。

## 原始来源

- [ReCode（ACL 2026）](https://aclanthology.org/2026.acl-long.2031/)
- [LEVER（ICML 2023 预印本页）](https://arxiv.org/abs/2302.08468)
- [CodeT（ICLR 2023 预印本页）](https://arxiv.org/abs/2207.10397)
- [DiffCodeGen（2026 预印本）](https://arxiv.org/abs/2605.20473)
- [Reason-Code（ACL 2026 Industry）](https://aclanthology.org/2026.acl-industry.30/)
- [Revisit Self-Debugging（2025 预印本）](https://arxiv.org/abs/2501.12793)
- [EvalPlus（NeurIPS 2023 预印本页）](https://arxiv.org/abs/2305.01210)
