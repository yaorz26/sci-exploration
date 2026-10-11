# P80 实际项目功能验证报告

## 目的

本阶段只回答一个问题：confuse PR #126 能否恢复成真实项目功能任务，而不是再写一个自足的路径函数。它服务于数据集构建，不是主问题 A 的拆分效果实验。

## 证据

- 仓库：`beetbox/confuse`，PR #126。
- 合并提交：`2c1f97e7b6aadbeb8bd6f112bd7ef965dbd977b0`。
- GitHub commit API 返回的直接父提交：`8b69242b8facdd7d1f87113693ea72017d61a0ff`；第二父提交为 PR 分支 `cf23f736e8c96f572cf0bd6d36774719d3ff872c`。因此先前把页面 base SHA 直接当作父版本的风险被排除。
- 两个版本分别保存到 `experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/{parent,merge}`，只取 `confuse/` 非测试源码及许可/配置文件；README 一次下载超时，未把它假装成已保存。
- 执行记录：`actual_project_v1/real_feature_diagnostics.json`；脚本：`actual_project_v1/run_real_feature_diagnostics.py`。每个版本独立子进程，使用临时应用目录和临时 YAML 文件，没有运行上游测试、读取 D1 隐藏数据或调用模型。

## 结果

父版本和合并版本各执行 6 个实际 API 诊断：

- 父版本的默认相对路径仍解析到应用目录；绝对路径保持不变。
- 父版本对 `ConfigSource(..., base_for_paths=True)`、`Filename(in_source_dir=True)` 和 `Configuration.set_file(..., base_for_paths=True)` 均返回 `TypeError`，说明新接口确实不存在。
- 合并版本接受三个新入口。`base_for_paths=True` 或 `Filename(in_source_dir=True)` 将相对路径解析到配置源文件目录；`in_app_dir=True` 覆盖回应用目录；绝对路径保持不变；`set_file` 传入该参数也能得到源文件目录结果。

这排除了“PR 只是文档或无效参数”的解释，也排除了“页面 base SHA 不能恢复父版本”的解释。它支持把该 PR 作为真实跨组件功能候选：`sources.py` 保存源目录语义，`templates.py` 消费该语义，`core.py` 暴露文件载入入口。

## 不能据此声称的内容

P78 的 18 次手写参考执行只说明适配器相互一致，不能说明忠实于项目。固定 POSIX 的路径包装没有经过真实项目 API 验证，已降为探索记录。P80 也没有证明拆分比整体好，没有模型结果，没有人工标签，正式 `dependency/state_scope/testability` 和 `split` 仍为 `null`。这个候选只能进入 `research_pool_only`，不能进入正式数据集或发布包。

## 下一步

不再扩展同一 PR 的边界格。下一步只把父版本、功能需求、4 个行为例和合并版本参考保存成一个候选任务定义，并把“行为可执行”与“结构标签未知”分开。若任务定义无法在不暴露合并补丁的情况下复查，就保留 P80 失败，不再添加包装任务。
