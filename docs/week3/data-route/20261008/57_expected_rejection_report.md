# P25结果：正确拒绝与局部可观察性是两项判断

F04公开需求明确要求非法scores元素或options.mode引发ValueError，不能返回部分结果。五个先手算输入由参考与另一结构实现各求值，共10/10符合预期，其中两个拒绝输入、4次正确拒绝。五条不同关系、10次双结构关系检查均符合登记预期。

有效scores从[1]改到[2.9]时，正常输出scores变为[2]，name仍为a；被忽略额外字段放入相似非法内容时正常输出全部不变。这两条可直接观察name投影。把scores改为["1"]或options.mode改为1时，完整结果均为题目要求的ValueError，name输入虽然未变，输出没有name值。两种合法拒绝的错误类型相等，也不能作为name隔离证据。五条关系中name可观察2、不可观察3，完整分母保留。

## 对P21门槛的限定

C04的公开声明域内没有要求solve抛异常；P21始终ValueError错误程序因此不可测且行为错误。不能把这项具体门槛复制为所有任务“函数异常必是行为错误”：F04本次明确异常域里的ValueError是正确需求结果。反过来，也不能将模型程序任意ValueError都合法化，必须核对该输入的预先需求预期。

测量至少保留需求符合性、结果种类（正常值/预期拒绝/非预期失败）、所选投影可观察性。正确拒绝可以支撑完整语义结果的关系，但它不提供缺失的局部字段值；不把拒绝后的不可观察降格为零变化，也不把全对象验证约束混称共享可变状态。正好说明“任务没有跨操作状态”不能替代“所有局部行为对所有合法异常输入都可独立观察”。

这是五个具体手算输入的有限证据，没有全域异常oracle或新的人工标签。隐藏案例读取0、模型/API/下载0、人工0，原20题307/切分/初标保持，旧C04实验不重跑。停止扩更多同类异常例子。

下一项P26整合保存证据，检验候选测量记录能否同时表达任务侧行为机会、生成后方案义务、输入域/拒绝门槛与总预算信息，而不把不同层次压成一个新二元标签。以可追踪案例映射和保留未测/null的管理端附件为退出结果，非正式冻结/可靠性或主问题A模型答案。

证据：`codeprm-reproduction/experiments/d1_expected_rejection_v1_20261008/{public_requirement_extracted.json,input_and_relation_freeze.json,input_results.json,relation_results.json,summary.json}`。实现`scripts/d1/probe_expected_rejection.py`，命令`python -B -X utf8 scripts/d1/probe_expected_rejection.py`；这些输入不加入原307。
