# 候选数据集隔离运行与行为契约复核报告

当前推荐的管理端候选成果是`decomposition-bench/experiments/d1_candidate_delivery_v4_portable_20261008/d1_project_initial20_v5_portable_candidate.zip`。它解决了旧包缺少上游运行依赖的问题。Python 3.13.7、Windows 11环境中，关闭第三方安装目录后，20题的参考实现及另一结构实现全部复跑通过；人工双审仍为0，数据集未正式冻结、未发布，问题A正式评测没有启动。

## 这一步改变了什么

P10的8/8检查只核实文件、案例数量、许可和ZIP字节。它没有验证离开原始工作区后的运行能力。本次发现两份管理端定义按目录层级定位`data/raw/.../repositories`，而该上游运行库没有装入P10包。换到新解压目录后，参考实现找不到上游库；不能用原工作区的成功结果证明交付包自足。

旧v2包和全部旧数据保留。新包在管理端增加固定commit的boltons、more-itertools、cachetools、confuse运行库与许可；confuse还需要PyYAML 6.0.3，补入17个纯Python文件和MIT许可，不带平台二进制扩展。四个库逐文件与已存固定commit下载ZIP及获取清单核对；PyYAML逐项与本机发行版RECORD核对，未重新下载或核验原始wheel，不宣称供应链安全审计。

原287个研究文件中285个逐字相同，只有`private/_curator/task_specs_snapshot.py`和`task_specs_expansion.py`改为包内相对依赖路径；两份原字节另存`ORIGINALS`。去掉这两处来源定位及搜索路径语句后，功能代码的语法树完全相同。所有题面、公开/隐藏/合并测试、切分、评分器、参考/另一结构入口、旧质量报告保持原字节。因此本次没有重新定义题目、改变旧模型成绩或把储备题改作开发题。

## 隔离运行结果与口径

| 检查对象 | 原v2包 | 可迁移v4包 |
| --- | --- | --- |
| 参考实现整题运行通过 | 0/20，均为缺库的ModuleNotFoundError | 20/20 |
| 另一结构实现整题运行通过 | 20/20 | 20/20 |
| 两种实现合计案例执行通过 | 307/614 | 614/614 |
| 从原工作区或site-packages借用已加载模块 | 0 | 0 |

每版20题×2实现＝40个子进程。每进程20秒、stdout/stderr合并1MiB限制；使用`-I -S -B -X utf8`，从包含中文名称的新目录解压，在空白工作目录运行，记录模块真实路径。只允许解压包内文件、标准库，以及精确登记的检查器自身。614是307个已存案例各运行两种实现，不是614个新案例，不是独立人工证据，也不是模型正确率。

这是Python依赖隔离检查，没有操作系统权限隔离或网络封锁；只验证本机Windows 11及Python 3.13.7，尚未验证Linux、其他Python版本。历史作者构建快照仍需原始研究工作区，不把“参考复跑自足”扩大为“离线从头重建全部数据”。

复核代码`verify_portable_delivery.py`的有效v2报告为14/14通过，覆盖原文件、补丁、来源许可、清单、ZIP哈希、示例与测试一致性、案例ID及40次复跑。第二遍仍由当前助手完成，不是独立人工复核。

## 行为条款与测试检查

对全部20题核对了公开题面例子与公开测试、合并表与公开/隐藏分表、每题case_id唯一，以及完全相同输入有无冲突期望。本次发现B02的`public_2`和`hidden_1`都为空操作，输入与期望完全相同。

原始口径继续保留：20题、307条案例记录＝40公开＋267隐藏。补充区别：跨公开与隐藏合计306个不同的逐字JSON输入；隐藏267条中266条未在本题公开案例中出现。这是精确输入去重，保留对象键顺序和数值写法，没有推断所有输入的语义等价类。重复项不会改变“所有案例通过才算整题通过”的主指标，但按案例计算比例时会重复计权，也不能把它当成额外隐藏验证证据。当前未删改旧数据；正式冻结时应在新版本处理或明确保留理由，不能追溯改写历史307口径。

另对B03、B04、C03、C04、C05、M05六题建立39条关键行为的需求原文—案例索引，包含ANSI完整/不完整码、查询解析及非可逆编码、调用键与LRU计数、实例隔离、布尔/数值类型、稳定排序等。对应已存输入与期望未发现新的明显条款矛盾。该索引不是全部20题的条款覆盖，也不是39项客观覆盖率；没有新增案例或模型评分。包含隐藏证据，只供管理端，不能加入真实人类盲审材料。

结构yes/partial/no仍是作者初标；“找到测试例子”不能证明“存在两个可独立验证的行为契约”，更不能证明拆分会提高成绩。独立人工真值、结构尺度一致性、污染未知与新颖性非穷尽等限制继续保留。

## 失败记录与修正

1. 首次隔离汇总误把检查脚本自己的`__main__`文件当外部依赖，错误汇总为0/40。原始输出保留；只豁免精确检查器路径，依据已存输出生成`corrected_summary.json`，得到参考0/20、另一实现20/20，没有重跑或改旧记录。
2. 可迁移打包v3误以为来源是git checkout，`git rev-parse`读到了父工作区HEAD而失败。来源实际为codeload ZIP解压，不证明来源commit有变化。失败中间目录及`BUILD_FAILURE.json`保留，v4改为已存下载ZIP逐文件验证。
3. 第二遍复核v1误把公开异常例子的`raises`字段当成`error`，导致M05检查失败。题面与测试本身正确；修复脚本并另存有效v2报告，旧报告保留。

这些错误影响检查/打包初版，不能省略，也不把修正后的程序复核当独立审查。

## 可复现入口

以下命令在`D:/yaorz/research/decomposition-bench`执行；输出目录不得预先存在，重跑须使用新目录。已执行的结果目录不覆盖。

```powershell
python scripts/d1/audit_package_portability.py --archive experiments/d1_candidate_delivery_v2_20261008/d1_project_initial20_v5_candidate.zip --output experiments/d1_portability_v2_isolation_20261008
python scripts/d1/package_portable_candidate.py
python scripts/d1/audit_package_portability.py --archive experiments/d1_candidate_delivery_v4_portable_20261008/d1_project_initial20_v5_portable_candidate.zip --output experiments/d1_portability_v4_isolation_20261008
python scripts/d1/verify_portable_delivery.py
python scripts/d1/audit_contract_traceability.py
```

构建脚本当前为有效v4实现，失败v3的原因另存，不以当前脚本冒称早期失败执行版本。正式成果的来源口径以原始清单和下载归档为准。

有效四份脚本的执行后副本及SHA256位于`experiments/d1_portability_v4_isolation_20261008/repro_sources_after_execution/`，明确标记post_execution_snapshot，不冒称执行前冻结或早期错误版本代码。

ZIP大小657887字节、372成员；SHA256：`671655dac37508b7a97d57da43593d9ff95a307551312aa00440c19f69c940d1`。包外`DELIVERY_CHECKSUMS_EXTERNAL.json`为压缩包校验入口，ZIP不把自己的哈希装入自己。包外复核报告和本报告追加披露后发现的限制，不覆盖ZIP。

证据：`experiments/d1_portability_v2_isolation_20261008/corrected_summary.json`、`experiments/d1_portability_v4_isolation_20261008/summary.json`、`experiments/d1_candidate_delivery_v4_portable_20261008/{PORTABILITY_PATCHES.json,RUNTIME_DEPENDENCIES.json,portable_delivery_verification_v2.json}`、`experiments/d1_contract_traceability6_v1_20261008/traceability_private.json`。

## 阶段审查与方向审查

P11的交付可迁移性目标通过，39条关键契约对照完成有限范围检查；未声称全部语义覆盖或总体研究完成。本轮模型0、下载0、训练/RL/收费/发布0，本地Qwen仍约98/100。管理包含private，只供管理端；真实双审仍只发另行生成的`reviewer_only.zip`，当前未发送。

选择以v4为当前可复跑的本地候选成果，保留v2存储完整性、运行失败及所有中间错误。后续继续全量需求条款/输入域证据复核，并在正式数据冻结时处理重复公开案例；不为此恢复模型扩量、不伪填人工标签、不重排储备。正式评测仍需要真实双审、数据/标签/协议冻结及预定任务和预算；包能运行不等于这些条件已满足。
