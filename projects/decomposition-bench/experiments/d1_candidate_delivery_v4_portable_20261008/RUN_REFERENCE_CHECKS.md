# 离线复跑说明（管理端）

解压后，在包的根目录使用Python 3.13.7。以下命令保持评分器原约定：

```powershell
python -I -S -B -X utf8 dataset/private/_curator/evaluate_candidate.py --candidate dataset/private/D1_B01/reference.py --cases dataset/private/D1_B01/all_tests.json
python -I -S -B -X utf8 dataset/private/_curator/evaluate_candidate.py --candidate dataset/private/D1_B01/alternate.py --cases dataset/private/D1_B01/all_tests.json
```

对manifest中的20个task_id各跑reference.py与alternate.py，总40次，307案例每实现一次。不要把private文件发给生成模型或盲审人类。上述命令仅用于可信参考/另一结构实现，不是未知代码的操作系统沙箱。评估被测候选须继续使用具有20秒/1MiB限制及冻结校验的项目执行器。
