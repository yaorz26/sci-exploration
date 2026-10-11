# P60：三参考在八新诊断的v2链路一致

之前尚未在v2执行的helpers/source_adapter各完成八个保存公开诊断，分别8/8；两者与P59保存whole返回/异常的严格类型比较各8/8。新增16solve、10次值类型门槛、6次异常比较及16次保存结果比较；没有重新运行whole、四错误控制或旧十二例。

结合P59的whole，v2参考验证为三个程序各8/8、共24次执行，但只覆盖同一组八新公开输入，不能称24个独立案例。P48旧三参考12/12、36次仍属于v1数值比较，不是v2结果。适配仍为count空域固定0、mode空域显式default的两个Stats对象；没有对实际源API次数插桩，不能用两行构造语句冒报运行调用数。

阶段审查：这组新边界没有发现两参考的空默认/整数类型/混合并列/长度/错误优先级差异，排除它们在本八行上不满足v2的解释。没有证明全域正确，也不是独立真值：三参考共享guard，来源适配与原Stats同源，人工0。候选标签仍null、未正式冻结或发布，原20/307/切分/初标/评分不变。

原始证据在`codeprm-reproduction/experiments/d1_typed_reference_agreement_v1_20261009/two_references_and_eight_saved_cases_frozen.json`、两份stdout/stderr、`two_reference_execution_results.json`、`summary.json`及`three_reference_v2_validation_manifest.json`。P59候选和原验证manifest保持原样，三参考新manifest另存。执行命令先为`python -B -X utf8 scripts/d1/probe_typed_reference_agreement.py --freeze`，再`--execute`。进程20秒/1MiB上限为可信本地限制，模型/API/下载/private0。

方向审查：停止新规则同一组验证。下一项以新四格有效输入和两个无效输入观察count/mode：有效域中能否只改变一个输出用途、为每个字段独立定位错误；共同拒绝时是否都应记为不可投影。目的为候选的任务侧可测证据，不规定helper，不回写原作者标签，不用存在两个字段便自动判yes。
