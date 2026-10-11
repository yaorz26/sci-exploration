# E_B09：同时报告数量与众数（另池公开候选）

在Python函数solve(payload)中，对一组离散观测同时提供两个用途不同的统计：数量用于规模检查，众数用于代表值选择。内部函数与计算次序自由，不要求先算数量，也不要求拆成helper。

payload须为普通字典，仅含必需的data和可选default。data须为列表，最多128项；每项精确类型只能是int或str，允许混合；bool、float、容器元素不允许。default省略时为None；显式值可以是有限JSON标量（None/bool/str/int/有限float），不能是数组或对象。

返回正好两个字段：count是列表长度（整数）；mode是频数最高的原值，并列时选择原列表中首次出现的值。整数1与字符串"1"分别计频数。空列表返回count=0、mode=default。输入不得改变，含列表次序、类型和字典键次序。

异常优先级：payload非普通字典抛TypeError；缺data抛ValueError；额外字段抛ValueError；data非列表抛TypeError；长度超128抛ValueError；data元素类型无效抛TypeError；default类型无效抛TypeError；default浮点非有限抛ValueError。无需固定异常消息。

适配声明：任务借鉴固定boltons Stats的count/mode用途。数量空域0和众数可选default用两个独立来源对象包装；长度上限、精确元素类型及异常是本候选明确增加的适配。不能称上游全部API原样复现。

本目录诊断全部公开，不构成隐藏确认集；目前仅12个新边界得到三结构实测，未覆盖上述全部无效组合/长度上限。正式标签、切分、人工复核未冻结；不并入原20题，不称模型效果。原评分器把1与1.0视为相等，但bool与数值区分，不能声称它强制count整数输出类型。


v2候选增量：输出的数量必须是int而非bool/float；众数保留被选原值或空域default的精确JSON类型，int与float不互换，合法float default继续允许。值类型门槛只适用于正常返回，合法异常比较异常类型，所有分支仍执行输入严格不变检查。执行器为evaluate_typed_candidate.py，不改原评分器。原12诊断/36执行仍为v1；当前只对八个新输入的whole及四错误控制开展v2验证，结果另存validation_manifest.json，另两参考未在v2运行，结构标签null/人工0/未正式冻结。
