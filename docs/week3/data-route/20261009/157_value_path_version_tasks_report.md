# P75：两种溯源语义的结果与限制

新增E_B13原值/结果路径、E_B14结果值/原路径；每题六个已公开输入、整体递归及分函数两种新参考，各6/6，共24次实际solve，24/24符合执行前手写期望、24/24输入不变。新增独特输入0，新增任务诊断记录12；P74旧参考调用0，复用其保存关系。两组干预×两参考×两任务=8个关系，8/8符合预测。

四候选在选定干预中的表现为：E_B11的匹配既不随factor也不随drop_null改变；E_B13只随drop_null改变；E_B14只随factor改变；E_B12两者均改变。这说明本适配中值与路径的语义消费可以分别定义；一个简单的“有依赖”字段会丢失这种区别。不能推成四个独立样本、通用依赖分类或拆分收益。

混合任务的自然项目需求尚未取得证据：原值/处理后坐标是溯源需求，处理值/原坐标是修改来源定位；代码能够实现不等于实际项目常需。四题同一助手、同一公开功能家族；六锚点非全域或人工双审。正式标签及切分null，模型/API/private/人工0，初始20题不改。本家族不再追加组合或重复检查，转另一来源的组内聚合依赖。

证据：decomposition-bench/experiments/d1_value_path_version_tasks_v1_20261009/execution_freeze.json、raw_execution.jsonl、summary.json。命令（decomposition-bench目录）：python -B -X utf8 scripts/d1/build_value_path_version_tasks.py prepare；python -B -X utf8 scripts/d1/build_value_path_version_tasks.py run。P74+P75共新增四候选、同六独特输入、24任务记录、60实际solve，不把60次执行说成60个新样本。
