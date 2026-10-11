# P27结果：接受条件含有参数注解的语法差异

B05/C03给定正确代码各有三个入口形式：普通solve(payload)、参数注解solve(payload:dict)、返回注解solve(payload)->object。函数体、helper、函数名、参数名/个数/调用方式保持。M0真实存在性门槛接受6/6；M2真实入口门槛接受4/6，只拒绝两份参数注解，返回注解控制2/2接受。

四份新完整注解程序在原公开两例各评，共8/8通过、输入未变；两原正确基线不重评，隐藏案例读取0。类型注解没有在这些程序中实施运行时参数检查，dict/object均为未被遮蔽的标准内置名。这里只证明有限公開相容，不是所有外部行为、模型发生率或效果。

## 具体接受条件

run_allin_pipeline.same_signature先确认入口片段只有预定顶层函数名，再比较FunctionDef.args的完整AST。参数annotation属于args，所以dict注解与冻结的空注解不同；返回annotation位于returns，未比较，因此允许。M0在extract_code后只确认function_names包含solve，行为错误在评分中再捕获。

门槛检验使用实际导入函数；M2送入的是单独entry片段，未将多helper的完整程序误判为入口撞名。未实例化NativeTokenizer、未调用transport、实际生成pipeline运行0。新代码、入口片段、公开测试及真实门槛来源在执行前冻结。

## 解释范围

同总预算是方法比较的一个条件，不能单独使整个流程成为“纯分解效应”。当前两臂的计划、轮次、固定helper契约及语法接受条件均属于具体策略。发现差异不意味着策略比较自动无效，也不能据两个手工例子把历史低收益归因于注解限制：P9保存的M2实际失败是helper名字改变，需要另核对，不能擅自救回或改成绩。

任务题面写solve(payload)，现评分器按位置参数调用；本反例保持payload参数名，也支持原keyword调用，因此不依赖把p改名解释为接口等价。helper已经由计划冻结的签名仍需严格匹配，不能因入口注解相容就放开真正的helper接口变化。接受一个AST也不是行为正确证明。

模型/API/下载0、人工0、无新隐藏/正式成绩、原流程代码未改。下一项P28在独立候选门槛中仅忽略入口参数注解，保留名称/个数/参数种类/默认值等约束；用公开正常表示与真实调用方式改变对照，以及P9保存helper失败验证。若不能保持约束，不扩复杂修补，记录失败并换路。

证据：`codeprm-reproduction/experiments/d1_method_gate_v1_20261008/{pre_execution_freeze.json,gate_and_public_results.json,summary.json}`及六份代码/入口。脚本`scripts/d1/probe_method_gate.py`，命令`python -B -X utf8 scripts/d1/probe_method_gate.py`。
