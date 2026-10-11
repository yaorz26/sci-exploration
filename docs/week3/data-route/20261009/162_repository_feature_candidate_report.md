# P77：真实功能请求筛选结果

我对原四来源做了定向公开历史查询，比较了 `confuse` PR #126、PR #142，以及 `more-itertools` PR #196/#440。PR #126 最适合进入下一阶段：它是已合并的真实功能请求，题目明确跨 `ConfigSource` 与 `Filename` 两个组件，解决配置文件目录与应用配置目录的相对路径基准；PR 元数据给出 parent `8b69242b8facdd7d1f87113693ea72017d61a0ff`、merge `2c1f97e7b6aadbeb8bd6f112bd7ef965dbd977b0`，改动路径含 `confuse/core.py`、`confuse/sources.py`、`confuse/templates.py` 和文档。PR #142 也是真实功能，但主要是新增环境变量来源，仍可作为后备方向；PR #196 是单函数 `map_reduce`，与刚完成的组上下文候选相近；PR #440 主要增加参数和迭代器缓存语义，暂不选。

当前保存的 `confuse` 提交 `bf42783301ac4e9c640328ec95486952fd599ce6` 已包含 `ConfigSource.base_for_paths`、`Filename.in_source_dir/in_app_dir` 和 `Filename.value` 的跨组件路径分支。非测试源码的直接语义是：相对路径若有 `cwd` 先用cwd；否则源文件存在且 `in_source_dir` 为真，或源的 `base_for_paths` 为真且未强制 `in_app_dir`，则相对源文件目录；否则有源文件或强制应用目录时相对应用配置目录。

这排除了“所有新增候选都是人工拼接单函数”的解释，但没有证明任务自然性已经充分，也没有执行模型。P77决定把一个真实合并请求的跨组件行为做成研究池候选，保留来源 URL、父/合并提交、修改路径和当前源码 hash；不读取变更测试，不把PR元数据当人工需求标注。

暴露纠正：P76执行后一次 `rg` 的排除tests通配写法未生效，输出了上游公开测试文件的约九条匹配行；随后读取了原公开D1_M04题面和公开例用于确认相关家族。没有读取D1隐藏内容、候选储备隐藏期望或模型提示，也没有用这些测试内容生成期望。该暴露已登记，不再声称“上游测试内容零暴露”；它不改变P76的执行结果，但禁止把该支路当作完全未见真值验证。

证据：`decomposition-bench/experiments/d1_repository_feature_candidate_v1_20261009/` 下四项PR metadata、PR126文件名metadata、PR126 parent/merge非测试源码快照及本报告。外部记录来自GitHub公开API，查询时间为2026-10-09；许可证沿用当前 `confuse` manifest 的MIT标识，最终发布仍未授权。
