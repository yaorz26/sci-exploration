# P47：离散候选必须明示适配和真实比较器

来源包装在六个输入上与事前逐值解析预期一致6/6；复用P44的18个输出交给原json_equal比较，whole/helper仍各6/6，wrong_tie仍5/6。没有重跑P44的三程序，新增为六来源包装（12 Stats对象）及一单对象空域对照，合计13 Stats对象/14属性查询。

两项新类型控制明确区分了评分方法：count=0被错误换成False、mode=0被错误换成False时，普通Python ==均接受，原json_equal均拒绝；第三项缺字段也拒绝。原六案例的成绩恰好没变，不说明原比较正确地覆盖了这些错误。因此P44的原证据只按原口径保留，本次才提供实际比较器证据。

公开Stats的空数据属性都返回同一个default：一个Stats([], default=-1)的count/mode都是-1。候选数量0、众数default=-1不能称与该单对象完全等价。明示来源包装为count取Stats(data,default=0).count，mode取另一Stats(data,default=题面值).mode；候选默认值只控制众数，数量总是列表长度。这是功能适配，不是上游原样复现。

预算口径更正：原机器summary的new_original_comparator_calls=22漏加六新参考比较，正确总数28＝6参考+18保存+3控制+1空域。count_clarification.json追加更正，原结果保留；脚本未来计数修正但不重跑。

阶段审查：排除“原Python相等和实际评分在所有错误上等价”；定位了来源默认值必须拆开的适配范围。仍未知混合整数/字符串并列、无效输入域/异常、完整参考封装能否一致，不以六例证明全域或人类标签。真实人工0，主A收益未知。

方向审查：P44限定修订完成，但离散功能仍只是待审扩展候选。P48先固定输入/输出/无效域契约，创建完整参考和另一个内部结构实现；少量新边界输入验证后才保留候选。原20/307/11—9不改，不填结构粗编码空格，不继续增加统计数量。

证据：`decomposition-bench/experiments/d1_discrete_adapter_fidelity_v1_20261009/`的sources_anchors_and_controls_frozen.json、summary.json、count_clarification.json。模型/API/下载/private/原测试0。每个结果的字段类型与空域口径可回查，不称独立人工审查。
