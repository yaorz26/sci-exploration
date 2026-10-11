# P28结果：限定入口修订可接受注解，不救回旧helper失败

离线候选只清除入口参数annotation，再复用原same_signature。六个P27正确给定入口全接受；七个手工调用形状变化仍全拒绝，共13种表示。原pipeline未改，helper仍使用严格冻结签名，新任务评分0；旧公开8/8沿用不重跑。

## 修订范围与控制

七对照为函数名、缺参、额外必需参、新增默认值、keyword-only、positional-only、varargs。14次最小调用分别试position和keyword。新增默认值仍支持两种调用，却被策略拒绝：这说明候选仍选择精确调用形状，不能称“只排除全部语义错误”或“最小充分门槛”。两种参数种类对照分别改变其中一种外部调用能力，拒绝原因和实际调用结果均保留。

候选接受注解也不等于证明任意注解表达式运行正确。原评分仍负责模块加载、行为与输入不变；此阶段只限定一项接受规则，不放开helper冻结接口、不承诺运行等价或模型成绩。

## 旧结果复核

P9保存的plan/两helper响应按原哈希读取，实际helper1严格门槛通过，helper2仍因顶层函数名不是预定_is_ansi_sequence而失败。这里复解析是为了区分“入口修订是否误救回旧结果”的新问题，没有模型重试或新增entry。旧M2整题0/1、1850真实tokens保持，入口阶段根本没有到达；不能将新语法修订归因于过去的模型失败或恢复成功。

原机器summary中的saved_P9_all_pass_unchanged字段名含混，false实际指旧all_pass值为false，不是结果改变。原输出保留，另写field_semantics_clarification.json明确actual_all_pass=false、outcome_changed=false；脚本未来输出字段修正，未为命名重跑实验。

模型/API/下载/隐藏评分0、人工0。限定修订达到本阶段目标，不继续扩语法变体或直接启用正式批量。下一项P29检验失败路径的计分语义：P9生成失败后的public/private passed=0是策略整题失败的记账值，还是实际已执行行为的失败数？这影响分层分析何种分母可报告、哪些计划属性仍未观察。

证据：`decomposition-bench/experiments/d1_entry_annotation_gate_v1_20261008/{pre_execution_freeze.json,forms_and_call_results.json,saved_P9_helper_review.json,summary.json,field_semantics_clarification.json}`。候选函数在`scripts/d1/probe_entry_annotation_gate.py`，命令`python -B -X utf8 scripts/d1/probe_entry_annotation_gate.py`；正式run_allin_pipeline字节保持。
