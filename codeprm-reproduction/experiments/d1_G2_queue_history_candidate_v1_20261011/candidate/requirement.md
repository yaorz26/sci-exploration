# 任务列表队首语义的有限功能任务（修订版 v2）

修订说明（v2，2026-10-11）：依据独立审查意见补齐三处口径——① 明确优先级方向；② 明确 `remove` 与异常的返回/抛出约定；③ 明确再次 `add` 的位置语义。修订前的 v1 已快照保存。

任务来源：`boltons` 官方模块 `boltons.queueutils`（官方文档 `docs/queueutils.rst`、模块 docstring 的 doctest、`CHANGELOG.md`）与固定父提交源码 `data/raw/d1_project_v1_20261008/repositories/boltons/boltons/queueutils.py`。

给定该模块的父版本，实现一个**有限域**的任务队列。内部数据结构、辅助函数、模块划分、是否复用 `heapq` 或 `bisect` 均自由。

## 一、优先级方向（必须按此实现）

**优先级数值越大越先出队**。`priority=5` 的任务排在 `priority=1` 之前。未传 `priority` 时视为 `priority=0`。优先级可为整数或浮点数（含 `0` 与负值）。

## 二、公开调用入口与返回约定

固定五个方法，名称与签名如下；评价只观察返回值与 `len`，不检查内部字段。
`_MISSING` 是"未传入该参数"的哨兵，**不等于 `None`**；`default=None` 与不传 `default` 是两种不同情况。

| 方法 | 签名 | 返回约定 |
| --- | --- | --- |
| `add` | `add(task, priority=None)` | 无返回值（返回 `None`） |
| `remove` | `remove(task)` | 成功时返回 `None`；任务不在队列时抛 `KeyError` |
| `pop` | `pop(default=_MISSING)` | 队列非空：返回并移除队首任务；队列为空且**传了** `default`（含传 `None`）：返回该 `default`；队列为空且**未传** `default`：抛 `IndexError` |
| `peek` | `peek(default=_MISSING)` | 与 `pop` 相同的三种情形，但不移除队首 |
| `__len__` | `__len__(self)` | 返回队列中的任务数（不含已 `remove` 的条目） |

**最小调用序列（用于交叉核对义务 2）**：

```python
q = PriorityQueue()
q.add('a', 1); q.add('b', 1)     # 同优先级，a 先入
assert q.peek() == 'a'
q.add('a', 1)                     # 对已在队列的 a 再次 add（更新）
assert q.peek() == 'b'            # a 被移到同优先级队尾
assert len(q) == 2                # 不产生重复条目
assert q.pop() == 'b'
assert q.peek() == 'a'
```

## 三、公开功能义务

1. **同优先级先入先出**：依次加入同一优先级的多个任务后，`peek`/`pop` 按加入先后返回。
2. **对已在队列的任务再次 `add` 视为更新**：该任务不产生重复条目（`len` 不变），并且**移动到与其优先级相符的位置**——在相同优先级下，先前加入的任务再 `add` 之后排在后来者之后。
3. **`peek` 不改变公开结果**：连续两次 `peek` 返回同一任务；`peek` 不减少 `len`。
4. **`remove` 移除指定任务**：被移除任务不再出现；`len` 相应减一；移除队首后 `peek` 返回下一个任务。移除不存在的任务抛 `KeyError`。
5. **更高优先级的任务压制较低优先级**：无论 `add` 顺序如何，`peek`/`pop` 始终给出当前优先级最高的任务；同优先级内按义务 1、2 的顺序规则。
6. **空队列语义**：见上表。

## 四、合法输入域

任务名为可哈希的短字符串；优先级为整数或浮点数；调用序列只包含上表五种操作。不纳入：线程安全、并发消费、`peek_n`、批量添加的扩展 API、性能或内存特性。

来源说明：同优先级先入先出、更新既有任务、`peek` 不弹出、`default` 语义与"数值越大越先出队"均来自官方模块文档、doctest 与实现；**"更新后移动到同优先级队尾"由官方实现语义给出，官方文档只承诺"更新优先级"，未逐字承诺同优先级下的新位置**——该差异是一处未解决边界，已登记。

状态：`research_pool_only`；`formal_labels=null`；`split=null`；真实人工双审 0；公开来源污染风险未知。
