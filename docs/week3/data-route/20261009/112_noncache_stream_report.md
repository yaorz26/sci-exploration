# P52：非缓存分片历史可以由持续解析或重算满足

六组执行前逐值终值锚点，三种结构共18新solve。持续HTMLTextExtractor、累计前缀html2text各6/6终值通过，六条完整轨迹一致（每结构14快照）；逐片html2text后拼接仅2/6。所有输入类型/内容/顺序保持，模型/API/下载/原测试/private0。

例如将字符实体拆成`A &am`与`p; B`，必须保留片段之间的信息才能得到`A & B`。逐片处理丢掉信息，持续解析和完整前缀重算都能恢复。支持固定boltons之外缓存家族的历史候选E_B10，但仍同boltons来源，不充新来源或独立统计样本。标签留null、不并原20/307，也不是模型生成效果。

底层计量分开：持续结构6解析器对象、14feed/14get_text，输入字符52；重算14对象、14feed/14get_text、字符85；逐片14对象、14feed/14get_text、字符52。总18solve不等42原API调用，实际feed和get_text各42次、共84次方法调用、34对象；字符量不是模型token/运行耗时/效率实证。

原始证据在`codeprm-reproduction/experiments/d1_noncache_stream_v1_20261009/`：六预期与来源先冻结，三worker原stdout/stderr与独立结果、结构/度量脚本哈希、summary单独保留。固定strutils SHA c5ecb7efd3b2e86f92545c18d8d72193f45a1bd1d0edaf3da65868aa0e8bcdda，commit4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d/BSD-3-Clause。源码算法不改，仅透传计数子类；模块实际路径boltons.strutils，111号简称不意味着顶层导出HTMLTextExtractor。

学到：这六组非缓存历史依赖并不强制helper共享可变解析器；完整前缀重算也是合法结构。排除：对所有允许片段逐片提取终值拼接足够。未知：中间快照两结构共享同一上游解析器，不是独立语义真值；特别是未结束实体/标签的输出时机可能依赖feed缓冲及EOF语义，不能因互证就叫需求已全清晰。

阶段审查：有限历史候选通过，正式需求/标签/全域未冻。方向审查：不枚举更多HTML语法；P53只对同六组的新“每累计前缀立即close”结构执行一次，复用P52正确轨迹，检验终值判分是否会漏中间时机错误。代码和问题新增才复用旧输入，旧三结构不重跑；模型预算/资源红线不变。
