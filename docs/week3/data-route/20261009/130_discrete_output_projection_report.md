# P61：正常输出可分别观察，共同拒绝没有字段投影

三参考对六个新公开输入各执行一次，共18solve，整体各6/6。四个正常输入形成数量2/3与众数整数4/字符串x的四格：count与mode各12/12符合事前逐值预期，12条保存输出关系均出现预定字段变化而另一字段不变。两个非法容器default在三参考中共同引发TypeError，共六次合法拒绝；没有正常字段返回，两字段共十二个投影记null/不可适用，没有把它们计成字段失败或通过。

24个构造输出控制来自十二个已保存正常返回，每份只错count或只错mode；全部24个完整输出被拒，24个都能定位变动字段而保留另一个字段正确判断。这些是输出对象比较控制，不是24个程序执行或模型候选。字段可分别观察由最终返回和输入变化见证支持，无需给定helper。

这项证据排除了“两个输出在本有效域只能同时变化”的解释，但没有证明算法、统计或全域独立。两个用途仍共享候选有效输入门槛；无效default即使对非空众数不用，也按公开规范共同拒绝。任务级正常域用途分离与共同有效域应同时保存，不因有两个字段自动把独立可测标签赋yes。原20/307/初标/切分/评分及候选标签null保持，人工0/主A效果未证。

调用口径：18solve，执行器12值门槛/6异常比较；正常投影24字段判断、关系24字段判断、输出控制48字段判断/24完整门槛。无helper追踪/再执行，P59八例及v1十二例零重跑，模型/API/下载/原测试/private0。三参考共享guard/同来源，手算由同助手事前保存，不是独立oracle。

原始证据在`codeprm-reproduction/experiments/d1_discrete_output_projection_v1_20261009/`，包括原六锚点冻结、执行代码hash、三个原stdout/stderr、`three_execution_results.json`、`normal_and_rejection_projections.json`、`twelve_saved_output_relations.json`、`twentyfour_constructed_output_controls.json`与`summary.json`。执行命令`python -B -X utf8 scripts/d1/probe_discrete_output_projection.py`，可信子进程20秒/1MiB，不是OS沙箱。

阶段审查通过，有限正常域与拒绝域分别记录。方向审查停止众数同类格，转B05的新问题：需求定义的先变换再筛选，是否允许在原树先选叶子再变换重映射路径？代数阈值逆变换在浮点边界是否有效？不重跑P13已保存的变换/筛选或融合程序，不推模型失败根因。
