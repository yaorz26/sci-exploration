# P36：helper被调用，返回值仍可能不参与最终结果

三个手工程序在同一输入上各调用目标helper一次，返回值的作用却不同。索引连接用返回索引排列行；P34恢复入口重算行索引、仅断言helper键值与结果相符；新程序调用helper后丢弃返回值，独立重算行索引。

新丢弃返回程序六手算6/6通过。首碰撞及reverse两输入、三个程序、错误返回与RuntimeError两干预，共12新干预求值，12/12符合先冻结机制预期。每次目标helper均调用一次；错误返回使索引连接产生错误输出2/2，恢复入口产生AssertionError 2/2，丢弃返回入口输出不变2/2。RuntimeError三种程序都传播，不能因此说返回值都用于结果。原两正常程序的四基线结果从P34保存复用；本轮总新完整程序调用18，旧参考/旧格/隐藏/模型/API0。

干预故意违反原helper局部语义，不能把错误后的行为当实际模型成绩。有限敏感性只描述这些程序在这两个输入的作用；不证明真实模型频率、全域数据流或因果收益，也不把事后方案属性变成前置分组。

阶段审查：同调用次数不能替代返回值作用，且返回约束与终值贡献应分开。方向审查：停止增加手工“正确/错误计划”数量，进入P37用真正保存的M2生成代码检验观察覆盖。候选不存在、入口在helper前失败、helper成功被调用等可能造成不同缺失；不能把没有调用统称提示旁路。

证据：codeprm-reproduction/experiments/d1_helper_runtime_influence_v1_20261008/{design_frozen,pre_execution_freeze,new_normal_results,intervention_results,summary}.json；脚本probe_helper_runtime_influence.py，执行python -B -X utf8 scripts/d1/probe_helper_runtime_influence.py。原模型成绩/数据集不改，约98/100调用、人工0保持。
