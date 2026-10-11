# D1真实项目功能任务研究候选成果

题目：面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究。

本版本交付两项具有有限公开行为证据的confuse项目包任务：PR126来源相对路径、PR142环境变量配置叠加。cache过期报告任务在pending，强时点/交付条款未解决。两项可用候选同仓库同配置家族，不是跨来源验证；三项管理候选/两来源，不是三项正式验收。原initial20的20题/307记录/11开发9储备未改、未装入本版本。

新实质产出是PR142有限功能任务及区分来源解析和项目整合的证据：三个公开场景×四组织共12worker，父0/3（缺入口），官方合并/独立模块各3/3，优先级遗漏2/3（冲突时错读文件host）。PR126既有完整/单模块替代8/8、source-only5/8/core遗漏7/8为保存结果，没有本轮重跑。

结构证据支持“行为连接义务不规定唯一内部拆法”。cache公开len/currsize可补清理，结果符合不能倒推返回前物理状态；正式结构标签/split null，人工双审0，主A模型收益关联未测。当前真实非缓存历史和不同独立用途缺口未填，公开源污染unknown，已登记偶然暴露不能抹去。

目录边界：public只有父包、有限需求和公开案例/来源。evaluation包含评价器、完整/替代/功能遗漏实现和旧机器结果；这些不向生成模型提供。pending保留未验收cache；evidence含结构、配对设计、资源和失败/暴露。各confuse父/参考包保留原MIT LICENSE。需求不规定helper数量/文件布局；任务是实际包API调用，不是JSON solve重写。并非完整Git仓库/完整PR/无污染/正式冻结版本。

依赖为本次Python3.13.7、PyYAML6.0.3；仅Windows本地已有证据，没有新的跨平台验证。列清单不执行评分：

```powershell
python -B -X utf8 run_evaluation.py --list
```

评价一个新的候选工作区，输出必须新建：

```powershell
python -B -X utf8 run_evaluation.py --task REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED --workspace <父包修改后的工作区> --output <新结果>.json
```

G4设计显示原M0+M2一题一seed需5—6请求；两有限题需10—12请求，B=6500每臂示例共26000token上限（非实际用量/费用，另需校准与烟测）。旧剩约2、DLL身份不符、真实人类0、任务/标签/协议未冻，当前不启动生成。M2项目适配/上下文尚未正式验证；不能以给定patch或手写通过补主A。

G2负结果：more游标重复已有公开M03且父恢复失败；boltons PR466公开merged=false/merged_at null，与本地CHANGELOG的fixed不同，不据非空merge_commit_sha造任务。保留全部失败/原分母。此目录是一次交付支撑；文件数/哈希/入口通过不是研究贡献或方法效果。未发布、未训练/RL、未新增付费或模型调用。
