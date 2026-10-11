# 本地公开行为复查入口

依赖：Python 3.13.7、PyYAML 6.0.3（本次实际环境）。父/合并快照来自官方提交，来源与哈希在上一层 `non_test_source_manifest.json`。保留原 MIT 许可证。

在本候选目录执行（输出名称须新建，不能覆盖本次机器结果）：

```powershell
python -B -X utf8 evaluate_env_source.py --workspace workspaces/feature --cases public_cases.json --output fresh_feature_result.json
```

`feature`、`alternative`、`parent`、`priority_omission` 是评价侧工作区。未来生成任务只可使用父源码、需求与公开案例；不能向模型提供合并/替代/遗漏实现、正确补丁或管理记录。当前未构造隐藏集，也未将候选加入 initial20。

本次实际运行三个公开场景×四个工作区，共 12 个隔离 worker；feature/alternative 各 3/3，parent 0/3（缺少入口），priority_omission 2/3（嵌套文件冲突时取错来源）。同助手构造、同 YAML Loader，非独立人工真值与全域等价。
