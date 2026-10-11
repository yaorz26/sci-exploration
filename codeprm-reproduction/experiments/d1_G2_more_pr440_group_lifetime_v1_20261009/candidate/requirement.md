# 相邻组变换在迭代生命周期内完成（修订版 v2）

修订说明（v2，2026-10-11）：依据独立审查意见补齐四处口径——① 公开用例中的 `keyfunc`/`valuefunc` 改为**显式给出**，不再靠反推；② 明确 `factor` 的含义；③ 明确 `reducefunc` 的调用时机与"已返回值保留"的判定规则；④ 删掉"不是要求任意惰性 reducefunc 都永久保存数据"这类不可判定的兜底表述。修订前的 v1 已快照保存。

来源：more-itertools PR440，官方合并 `78405e9b24d0ccdd67785136ecd56774f38ae95e`，直接父 `38d070c9252d2138dbd86f8f85b9970741401cb6`。PR 标题/正文初称 `groupfunc`，合并版本的公开 API 参数名为 `reducefunc`，任务采用实际公开 API 名。不要求复制合并实现或固定内部 helper/存储结构。

给定父包源码，为 `more_itertools.groupby_transform(iterable, keyfunc=None, valuefunc=None, reducefunc=None)` 增加整组变换：仅相邻且 key 相同的项分为一组，`keyfunc` 计算 key，`valuefunc` 先变换组内每项，`reducefunc` 接受该组变换后的可迭代值，其返回值作为外层 `(key, result)` 的 `result`。

## 一、回调的调用时机（必须按此实现）

- `reducefunc` **在该组被外层消费到时调用一次**，入参是该组经 `valuefunc` 变换后的可迭代值。
- `reducefunc` 返回之后，对应的 `(key, result)` 即可被外层继续消费；**返回值一旦产生就不再变化**，即使外层迭代继续前进、后续组继续被消费。
- `keyfunc`/`valuefunc` 未提供时保留父默认行为（key 为元素本身、value 为元素本身）。`reducefunc` 未提供时，保留父 API 的懒组可迭代结果与共享底层迭代器的行为，**不得**为新功能把全部组永久物化。

## 二、合法输入域与术语定义

- 有限可迭代数据；纯函数式的 `keyfunc`/`valuefunc`（无副作用）。
- `reducefunc` 限定为两类：`list`（收集整组）或 `sum`（数值求和）；两类都必须在调用时**完整消费**传入的可迭代值。
- `factor`：仅出现在公开用例中，指 `valuefunc` 使用的一个整数缩放系数，即 `valuefunc = lambda x: x * factor`；它**不是** `groupby_transform` 的参数。
- 同 key 的非相邻组保持分开，不排序、不合并。

## 三、公开功能义务

1. **相邻分组**：只有相邻且 key 相同的项进同一组。
2. **valuefunc 先于 reducefunc**：`reducefunc` 收到的是经 `valuefunc` 变换后的值。
3. **整组变换结果作为 result**：`reducefunc` 的返回值即 `(key, result)` 中的 `result`。
4. **已返回值保留**：`list`/`sum` 这类完整消费型回调产生的结果在外层继续前进后**仍然可用且不变**；外层迭代推进不得把先前已产出的 result 变成空值。
5. **无 reducefunc 时保持父行为**：返回懒组可迭代值，行为与父版本一致。
6. **回调默认值**：`keyfunc`/`valuefunc` 省略时保留父默认行为。

## 四、不纳入范围

不测无界流、内存/效率、任意带副作用的回调、非 list/sum 的自定义惰性 reducer、以及 `groupby_transform` 以外的 API。

## 五、公开用例（内嵌，供在文内核对）

以下三例即评价所用公开用例；`keyfunc` 与 `valuefunc` 显式给出，`factor` 是 `valuefunc` 的整数缩放系数。

| 用例 id | 输入 items | keyfunc | valuefunc | reducefunc | 期望输出 |
| --- | --- | --- | --- | --- | --- |
| `retained_lists_after_outer_exhaustion` | `[('a',1),('a',2),('b',3),('a',4)]` | `lambda x: x[0]` | `lambda x: x[1] * 10`（factor=10） | `list` | `[('a',[10,20]), ('b',[30]), ('a',[40])]` |
| `group_sums` | `[(0,2),(0,4),(1,1),(1,3)]` | `lambda x: x[0]` | `lambda x: x[1] * 1`（factor=1） | `sum` | `[(0,6), (1,4)]` |
| `no_reducer_keeps_parent_lazy_groups` | `[('a',1),('a',2),('b',3)]` | `lambda x: x[0]` | `lambda x: x[1] * 1`（factor=1） | 不传 | 见下 |

第三例的观察序列（`keyfunc`/`valuefunc` 均显式给出，`reducefunc` 省略）。
**两个序列都要做，结果不同，这正是"惰性"的可观察含义**（已按上游实测校正：`experiments/d1_G3_fidelity_probe_v1_20261011/detail_probe.json`）：

```
# 序列 A：先消费第一组，再推进 → 组内元素保留
it = groupby_transform(items, keyfunc=keyfunc, valuefunc=valuefunc)
first_key, first_group = next(it)
list(first_group)              # [1, 2]（先消费）
second_key, second_group = next(it)
list(second_group)             # [3]

# 序列 B：先推进到第二组，再回头消费第一组 → 第一组已空
it2 = groupby_transform(items, keyfunc=keyfunc, valuefunc=valuefunc)
first_key2, first_group2 = next(it2)
second_key2, second_group2 = next(it2)
list(first_group2)             # []（推进后再消费）
list(second_group2)            # [3]
```

即：不传 `reducefunc` 时组是**共享底层迭代器的惰性视图**——未推进前消费可得元素，一旦推进到下一组，先前未消费的组变为空。**不得**把组实现为一次性物化的列表（那样序列 B 会错误地返回 `[1,2]`）。

**义务 4「已返回值保留」的观察口径**（必须按此判定）：用第一例。先把外层迭代**完全消费并物化**为列表 `out = list(groupby_transform(...))`，再检查 `out` 中各 `result` 是否仍等于期望的列表。另用第三例的**序列 A/B 对照**判定惰性：序列 A（先消费）必须得到 `[1,2]`，序列 B（先推进）必须得到 `[]`。义务 4 只由第一例的 result 保留判定；第三例判定的是"懒组不物化"，两者不要混用。

状态：`research_pool_only`；`formal_labels=null`；`split=null`；真实人工双审 0；模型效果 0；公共污染 unknown；既有暴露另存。
