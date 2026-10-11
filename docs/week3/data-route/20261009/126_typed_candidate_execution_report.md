# P59：类型门槛需要与异常分支和输入检查合用

候选v2另版执行链在八个新公开输入上完成五程序各一次的运行，共40solve。正确whole在旧数值规则与v2完整规则下均8/8，包含三个合法异常、合法float/bool/int default和128项并列众数。八输入未重用v1十二诊断，旧36次执行仍记为v1，不是v2重复通过。

四个人为控制的结果与事前预测一致。float count在旧规则8/8，在v2为3/8，仅三个异常通过；众数/default数字类型替换在旧规则8/8，在v2为5/8，三个同数值的类型漂移被拒。先算正确结果再逆转输入的程序，单看返回内容8/8，包含输入不变检查则6/8，两个非空列表修改被拒。错误异常类型的程序5/8，三个应抛TypeError/ValueError的输入均被拒。

仅适用于value的类型函数不能单独替代完整执行器：忽略异常分支时，正确whole只会接纳五个正常返回，5/8；忽略输入检查时，修改输入控制的内容仍8/8。本阶段执行器将正常value交给类型门槛，将error交给异常类型比较，同时保留严格的输入类型、内容、列表及字典键次序检查。JSON序列化后int/float仍可区分，合法4.0 default没有被拒。

调用口径为40solve、25次值类型门槛、15次异常比较、40次旧规则比较及40次输入比较；这些判定次数不是模型调用。全部运行使用可信本地子进程，每进程20秒/1MiB上限，非OS安全沙箱。模型/API/下载/原测试/private0、人工0。五程序共享whole基础，四错误控制是人为构造，不代表模型缺陷频率或独立oracle。

原始证据在`decomposition-bench/experiments/d1_typed_candidate_execution_v1_20261009/eight_new_cases_and_five_programs_frozen.json`、`five_execution_results.json`、五份stdout/stderr以及`summary.json`。执行命令为`python -B -X utf8 scripts/d1/probe_typed_candidate_execution.py`。

可运行v2公开候选保存于同目录`candidate_v2/`，含完整需求、原需求副本、任务/来源/许可、原诊断副本、新八诊断、三份参考、四错误控制、类型函数和独立执行器。`validation_manifest.json`明确当前whole为8/8，另两参考尚未在v2执行。原评分器、v1候选、原20题/307记录/11—9切分及作者标签不改，候选结构标签仍null，未正式冻结或发布。

阶段审查：排除了“值比较函数已足以替代整条执行链”，也排除了“标准JSON序列化使本输入的int/float区别必然消失”。有限八输入不足以保证全域、全部异常优先级或另两参考的类型保持。方向审查：下一项只验证尚未在v2执行的helpers/source_adapter两参考，并记录来源适配口径；不重复已通过whole或旧十二例，也不再扩四种错误控制。
