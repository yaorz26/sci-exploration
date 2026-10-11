# P43接续点：精确比较拒绝保存的浮点差异，候选精度仍未冻结

已保存原P42一个差异与原evaluate_candidate.py完整源码哈希/函数节点。只在独立命名空间执行原json_equal函数，对保存对象及控制值比较；没有运行Stats、任何solve候选或原案例，没有private读取。

八个比较对一次执行：保存的两完整输出不同；同值复制相同；1与1.0相同；False与0不同；方差加1e-3不同；NaN自身不同；Infinity自身相同；默认ordered_objects=False下字典键顺序反转相同。非有限数两个对只是孤立函数的Python值控制，不是标准JSON，也不能据此称整个评分器接纳NaN/Infinity。

明确证据是：现有比较器不容纳4.44e-16保存差异。E_B08新候选尚未规定逐位复现上游或数值精度，故不能把这个结果直接称“原评分器错误”，也不能把候选局部1e-12诊断容差当正式通过条件。原20需求/规则/成绩未变。

下一独立动作：给E_B08限定输入数值域、输出有限性/类型及精度，并比较绝对和相对规则各自会允许什么；至多使用已保存差异与超差控制，不扩大随机样例。如果无法清晰限定或需要大范围数值研究，候选保留研究池、换数字表示无歧义的功能，不沿此支路无限消耗。

P43尚未完成：已有原比较器证据，未来数值契约与方向审查待完成。证据目录`decomposition-bench/experiments/d1_numeric_contract_comparison_v1_20261008/`含`difference_and_comparator_frozen.json`与`original_comparator_observation.json`。模型/API/新下载/任务求值/隐藏读取均0。
