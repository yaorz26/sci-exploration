# PR440有限公开行为入口

依赖：Python 3.13.7，本候选只使用包源码和标准库。父/合并源文件、MIT许可和提交哈希见上一层 `source_manifest.json`；没有读取上游测试。

```powershell
python -B -X utf8 evaluate_group_lifetime.py --workspace workspaces/feature --cases public_cases.json --output fresh_feature_result.json
```

本次实际运行三个公开场景×四个隔离工作区，共12个worker：父1/3（仅无reducefunc旧行为通过），合并3/3，独立组织3/3，延迟归约控制1/3。控制的两个失败是外层推进后旧组已空/归约值为0；它不破坏无reducefunc旧行为。结果只说明有限回调域，不证明任意回调或全包语义。

需求使用合并公开API的实际参数`reducefunc`，保留PR正文标题`groupfunc`的口径差异记录。未来模型只能看父包、该需求和public_cases；合并/替代/控制和机器输出留在评价侧。
