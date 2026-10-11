# PR126直接公开入口遗漏反例计划

状态：草案，三轮审查完成前不构造工作区、不运行行为。宏观G3新缺陷最小干预，继承模型/预算/泄漏/内部自由/版本红线。

## 具体未知与结果

H1旧八项诊断能排除YamlSource公开参数遗漏；H2遗漏直接API但实现set_file间接路径可全部通过；H3补充观察绑定内部组织。要得到新控制旧8/8、新直接入口0/1，同时完整与独立组织新各1/1的实际证据，或保存与预测不同的失败；不从有限结果推全域完备或模型优势。

## 实施步骤

1. 从稳定v2评价目录的complete复制非测试项目工作区到新控制；只修改YamlSource签名/父调用和Configuration.set_file：YamlSource保持旧参数形式，set_file加载后设置base_for_paths再加入来源。保留ConfigSource、Filename和所有其他功能；记录逐文件hash和精确diff。
2. 冻结一个新公开场景：真实临时应用目录与不同源目录，文件path: assets/a.txt；直接YamlSource(filename, base_for_paths=True)，Configuration.add后Filename读取应返回源目录/assets/a.txt。控制预测TypeError且失败；complete/alternative预测通过。期望来自题面/目录，不采参考输出。
3. 只对新控制运行旧evaluate.py一次，保存八条原始结果；两个旧正确工作区不重跑旧评价。三个工作区各运行新场景一次，隔离导入、确认实际包路径，保存异常/环境/进程失败，最多4个worker启动、11个case判断。
4. 反例若成立，保留独立增量评价器与公开场景；旧定义/旧评分/稳定v2包不修改，合并目录不再打包。报告旧观察的精确限制和新增发现，不给正式标签。
5. 保存阶段/方向审查、状态/账本/记忆，再完成三轮后续深挖。禁止自动扩PR126其他优先级网格。

## 资源、失败和允许范围

20分钟、两次实质尝试、模型/下载/人工0，非测试allowlist仅PR126 stable v2 complete/alternative/evaluate及公开requirement。输出`experiments/d1_G3_pr126_entry_gap_v1_20261009`，排他新文件。新控制若旧评价失败，不以结果为导向反复调控制；只有明确机械修改错误允许一次修复，保留首失败。新场景若误拒alternative，判H3风险，先保存差异并重审，不向参考靠拢。输入无初始20隐藏/上游测试。formal_labels/split null。
