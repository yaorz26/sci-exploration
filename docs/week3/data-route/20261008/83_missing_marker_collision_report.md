# P38：同一返回值可来自不同正确语义分支

B06允许查询返回任意JSON值；路径缺失、未给default时则返回{error:'missing'}。tree={x:{error:'missing'}}且查询x时，正确结果是找到的合法对象；tree={}查询x时是缺失标记，两者都返回[{error:'missing'}]。找到null与缺失后返回default=null也相同。因此仅凭返回对象的error字段或输出相等，不能判定路径缺失/相同语义分支。

十个事先冻结输入由两原实现求值20次，手算20/20符合、输入均保持；五成对关系5/5符合。两个碰撞关系的分支标签来自公开需求手算，不是从输出倒推；另三关系对同tree/path使用default=0/1：找到marker/找到null时返回不变，缺失时返回分别0/1。一个默认值可能撞上合法数据，但两个不同默认值的对照排除了这些具体歧义。完整声明规则下找到分支忽略default、缺失分支返回default；实际程序还须满足绝对行为，不把关系通过自动当正确。

这里error对象是返回数据，不是函数异常；未给default的缺失是合法结果，不按执行失败删分母。该观察边界有别于F04合法抛异常后没有局部name输出，也不同于P21始终抛错的退化程序。它影响任务可观察行为如何定义，不能回写旧结构标签成可靠真值。

原实现只从curator AST定向提取函数，不执行规格/案例列表，不将隐藏描述输出到工具。公开需求、提取代码、上游文件及脚本哈希先冻结；旧307/有限格/隐藏新读取/模型/API0。P31既有暴露限制仍在，不称未见储备确认。

阶段审查：两个观测碰撞及默认干预区分竞争解释，未知/分支推断口径保留；不是模型效果。方向审查：停止继续增加任意JSON标记反例，转P39核对这些新测量边界相对功能级评测文献的贡献，以免已有研究已覆盖同一框架却被当成创新。主问题A和数据集拟成果定位保持，不用文献检索替代模型效果证据。

证据：decomposition-bench/experiments/d1_missing_marker_collision_v1_20261008/的first_hand_collision/inputs_and_relations/pre_execution_freeze/input_results/relation_results/summary与提取函数；执行python -B -X utf8 scripts/d1/probe_missing_marker_collision.py。原20题307记录/作者初标/历史成绩不改，模型调用约98/100、人工0。
