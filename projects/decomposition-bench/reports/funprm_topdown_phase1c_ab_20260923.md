# FunPRM Top-down 阶段 1c A/B 配对结果

日期：2026-09-23。结论状态：`fail_stop`。本报告只使用开发题公开测试与结构审计；private 程序评测和测试执行均为 0。

## 一句话结论

JSON 函数体确定性装配和论文启发的 few-shot 单轮 CoF 都没有达到扩量门槛，因此本地 7B top-down 分支按预注册停止；后续回到已有正向选择信号的 helper-first FunPRM，不再设计第三套 top-down 提示。

## 协议与数据修订

- 模型：`qwen2.5-coder:7b`，本机模型 ID `dae161e27b0e`；seed=`20260923`。
- 两路各 20 题 × 2 候选，共 80 次请求；temperature=`0.4`、`num_ctx=8192`、`num_predict=1536`，零重试。
- 固定源：`codeparrot/apps@21e74ddf8de1a21436da12e3e653065c5213e9d1`。Hugging Face 主站不可达后，使用支持相同 revision 路径的 `https://hf-mirror.com`；源文件返回 107,101,272 字节的目标 JSONL。
- introductory 在 `skip_matching=140` 后取得 30 道候选。interview 在 `skip_matching=100` 后为 0 道，因此在任何模型调用前按修订 01 改为 competition：`skip_matching=40` 后取得 30 道候选。两层清理后各取 10 道全新题。
- 清理阶段 60/60 道候选保留，没有发现题面同时明示输入与输出的 private 样例。最终 20 题与全项目既有 `apps-train-*` 题号排除表无重叠；冻结文件 SHA-256 为 `a3deed66b7654b17a106fbb03af1f0ea9886874f2b6a0c4a0d60788d990b065a`。

## 正式结果

| 方法 | 结构有效候选 | 结构覆盖 | 公开池 oracle | 有效候选平均公开通过率 | 是否过线 |
|---|---:|---:|---:|---:|---:|
| A：JSON 函数体 + 确定性装配 | 16/40 | 11/20 | 2/20 | 0.3010 | 否 |
| B：few-shot 单轮 CoF | 16/40 | 10/20 | 3/20 | 0.4126 | 否 |

预注册通过线是结构覆盖至少 `16/20` 且公开池 oracle 至少 `4/20`。两路均同时失败。

分层结果：

| 层 | A 结构覆盖 | A 公开池 | B 结构覆盖 | B 公开池 |
|---|---:|---:|---:|---:|
| introductory 10 题 | 8/10 | 2/10 | 5/10 | 3/10 |
| competition 10 题 | 3/10 | 0/10 | 5/10 | 0/10 |

逐题配对结构覆盖为：两路都有 6 题、仅 A 有 5 题、仅 B 有 4 题、两路都没有 5 题。公开池命中为：两路都有 2 题、仅 B 有 1 题、其余 17 题均无全通过候选。没有证据支持把一条路线带入后续 top-down 候选池门控。

## 失败解释与成本

- A 的 24 个无效候选中，合同审计最常见的是一个候选内多个函数的签名不合法、未知依赖、入口不在首位和 helper 不可达。错误计数按函数/规则累计，不能把 `invalid_signature=65` 误读为 65 个候选。
- B 的 24 个无效候选主要仍是顶层函数数量不足（16 次规则命中）和嵌套函数（6 次）；这与阶段 1 的单函数退化方向一致。
- 两路都没有请求失败。A 使用 prompt/output token=`28,762/16,034`，B 为 `36,942/10,230`。总墙钟时间 `834.998` 秒。
- competition 两路公开池均为 0，说明较难题上不仅是格式问题，语义候选池也没有达到最低信号。本轮只是工程筛选，不能与旧 interview 数字直接横比。

## 审计偏差

- 数据准备前的一次旧记录检查在终端意外显示了本地非公开字段；这些值没有进入本轮题目选择、提示、生成、公开筛选或结论。之后的旧数据排除只读取题号。本轮 20 题均为新的 problem ID，因此该意外不提供本轮答案信息。
- 原预注册的 interview 层不可执行；替换为 competition 的决定在模型调用为 0、A/B 结果尚未观察时冻结，详见修订 01。候选数、总题数、调用预算和通过线未改变。

## 决定

阶段 1c 记为 `fail_stop`：停止本地 `qwen2.5-coder:7b` top-down 提示分支，不扩到 top-down 100+ 训练题，不为它训练评分器，也不启动 RL。

项目总目标继续：已有 helper-first 轨迹的候选池在未触碰 30 题上有 `18/30` pool oracle，相对固定首候选 `8/30` 和随机期望 `9/30` 存在明确选择空间；真实前缀生成式 PRM 已兑现 `15/30`。下一阶段只扩大这条已验证机制路线，同时明确它不是论文 top-down 轨迹复现。

## 证据

- 原协议：`experiments/topdown_ab_phase1c_20260923/preregistration.md`
- 数据修订：`experiments/topdown_ab_phase1c_20260923/amendment_01_competition_stratum.md`
- 冻结切分：`data/splits/topdown_ab_phase1c_20260923/apps_train_intro10_competition10_manifest.json`
- 正式摘要：`data/processed/topdown_ab_phase1c_20260923/qwen25coder_7b_n2_seed20260923_v1_summary.json`
- 机器审计：`data/processed/topdown_ab_phase1c_20260923/qwen25coder_7b_n2_seed20260923_v1_audit.json`
- 可复算脚本：`scripts/analyze_topdown_ab.py`
