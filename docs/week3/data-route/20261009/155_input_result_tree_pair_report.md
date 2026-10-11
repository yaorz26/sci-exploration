# P74：新增任务与结果

E_B11在输入原树上查找，E_B12在变换结果树上查找。两题已各有中文需求、task.json、六公开例、三种参考，公共源码与BSD-3-Clause许可随研究目录保存。正式标签及切分null，人工0；同一家族，不并入原20题。

执行前冻结于2026-10-09T06:24:19.311993+00:00，完成于06:24:44.983068+00:00。六个新公开输入形成12个任务诊断记录；整体递归、分函数、源库适配各任务6/6，共36次实际solve、36/36符合期望、36/36输入不变。实际函数插桩为research12、remap24，后者含research内部再调用remap，并非宣称任务需要这个次序或次数。

两组干预共三参考×两任务×两关系=12个保存结果比较，12/12符合预测。乘数从1变2，原树匹配不变，结果树匹配的值与成员改变；[null,4]删除null，原树匹配路径仍是['a',1]，结果树路径为['a',0]。两个任务在六输入的factor_two、drop_null、factor_zero、factor_negative四例不同，每参考均4/6。

因此在所选六锚点中排除了“只改措辞、输出始终相同”；公开API适配与两种手写参考一致，降低了单个实现错误的解释，但三参考同一助手，不能称独立真值。没有要求结果查找必须先物化树，合法的原树计算与路径映射仍可用。

新贡献是两个可执行候选及可复查的值/路径依赖证据，模型效果、全域正确性、正式标签及完整项目集成均未验证。模型/API/下载/private/人工0；initial20 manifest SHA不变。下一问题是值与路径版本是否可分别构成明确的任务语义，按156号补两个混合版本，使用这六个公开输入只执行新任务，旧程序不重跑。

证据目录：codeprm-reproduction/experiments/d1_input_result_tree_pair_v1_20261009/，execution_freeze.json、raw_execution.jsonl与summary.json。命令（codeprm-reproduction目录）：python -B -X utf8 scripts/d1/build_input_result_tree_pair.py prepare；python -B -X utf8 scripts/d1/build_input_result_tree_pair.py run。固定来源及约束见154号。

口径纠正沿用154号：P72的机械一轴0不构成主问题A不能推进的证据；P20原C03每参考11例、合计33例；P73仅文本设计。P71停止，不再连续增加声明、包装或静态gate支路。
