# 相邻组变换在迭代生命周期内完成

来源：more-itertools PR440，官方合并`78405e9b24d0ccdd67785136ecd56774f38ae95e`，直接父`38d070c9252d2138dbd86f8f85b9970741401cb6`。PR标题/正文初称groupfunc，合并版本的公开API参数为reducefunc，任务采用实际公开API名。不要求复制合并实现或固定内部helper/存储结构。

给定父包源码，为`more_itertools.groupby_transform(iterable, keyfunc=None, valuefunc=None, reducefunc=None)`增加整组变换：仅相邻且key相同的项分为一组，keyfunc计算key，valuefunc先变换组内每项，reducefunc接受该组变换后的可迭代值，其返回值作为外层 `(key, result)` 的result。

有限合法域：有限可迭代数据、纯key/value回调，以及在调用时完整消费传入组的list或数值sum回调。同key的非相邻组保持分开，不排序或合并。reducefunc完成的list/数值结果即使外层迭代继续前进，也应保留已返回值；不是要求任意惰性reducefunc都永久保存数据。

未提供reducefunc时，保留父API的懒组可迭代结果及共享底层迭代器的行为，不能为新功能擅自将全部组永久物化。keyfunc/valuefunc未提供时保留父默认行为。内部可以组合既有groupby，也可以另组织模块，但外部调用与迭代结果相同。

本候选不是完整more-itertools仓库任务，也不测无界流、内存/效率或任意回调副作用。正式labels/split null，research_pool_only；人工双审/模型效果0，公共污染unknown，既有暴露另存。
