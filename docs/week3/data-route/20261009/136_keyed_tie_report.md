# P64：合法并列代表可能被精确来源答案误拒

未来abs-key诊断的四新输入、两方案各一次，共八次方案函数求值，来源minmax四次。事前逐值预演8/8符合，输入保持、公开成员和极值key语义8/8符合。两个并列最大key输入上，来源与builtin的最大代表不同；另外两个唯一极值输入一致。

在`[0,5,-5]`上来源返回minimum=0/maximum=-5，builtin返回minimum=0/maximum=5；在`[0,-5,5]`上符号选择相反。公开docstring已说明最大key并列不保证首次代表，这两个原整数都在各自输入中、绝对值均为最大key。固定来源精确预期给来源4/4、builtin2/4；后者两个拒绝属于多加了来源内部的选择约束，不是所声明公共语义下错误。

所有四行最小key唯一，故没有推断来源未明示的最小并列规则。本研究variant明确允许任一并列最大原代表；当前E_M07不暴露key，精确整数同值并列仍是同一个返回值，不受此反例影响。没有修改当前候选域、原20/307/储备/初标/评分。人工0/模型效果未知，也不估计并列频率或模型误判率。

计数澄清：脚本原字段`solve_calls`/`new_solve_calls=8`沿用了行为求值命名，但实际执行的是两`fn(data)`方案函数各四次，不是`solve(payload)`入口。已另存`evaluation_unit_clarification.json`：实际solve入口0、方案函数求值8、来源4；原字段/原输出不覆盖。契约8solve上限据实际口径读为八个方案行为求值，这项口径偏差保留，不混入P61—P63的54次实际solve入口。

原始证据在`codeprm-reproduction/experiments/d1_keyed_tie_v1_20261009/four_inputs_and_tie_predictions_frozen.json`、原stdout/stderr、`two_execution_results.json`、`summary.json`及上述澄清。命令`python -B -X utf8 scripts/d1/probe_keyed_tie.py`；可信进程20秒/1MiB，模型/API/下载/旧六例/原测试/private0。

阶段审查：排除了“来源与builtin总返回同代表”，两个合法差异支持避免来源实现定义唯一预期。仅绝对key相同还不足以判合法，输出须来自原输入且保持整数类型。方向审查：下一项只用保存输入/返回，冻结成员、类型及极值键错误控制，验证一个未来限定域比较规则；不扩所有key或刷新现有候选，不再运行两个已通过方案。
