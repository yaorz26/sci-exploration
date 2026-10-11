"""参考实现：完整组织。内部保存 (优先级, 序号, 任务) 并按 (优先级, 序号) 排序。

约定：优先级数值越大越先出队，与官方模块一致；同等优先级按序号先入先出；
对已在队列的任务再次 add 视为更新，先移除旧条目，再以新序号重新入队。
"""


class PriorityQueue:
    def __init__(self):
        self._items = []          # [(priority, seq, task)]
        self._seq = 0

    def _ordered(self):
        return sorted(self._items, key=lambda it: (-it[0], it[1]))

    def add(self, task, priority=None):
        if task in [it[2] for it in self._items]:
            self._items = [it for it in self._items if it[2] != task]
        priority = 0 if priority is None else priority
        self._seq += 1
        self._items.append((float(priority), self._seq, task))

    def remove(self, task):
        for it in self._items:
            if it[2] == task:
                self._items.remove(it)
                return
        raise KeyError(task)

    def peek(self, default=None):
        if not self._items:
            if default is None:
                raise IndexError('peek on empty queue')
            return default
        return self._ordered()[0][2]

    def pop(self, default=None):
        if not self._items:
            if default is None:
                raise IndexError('pop on empty queue')
            return default
        item = self._ordered()[0]
        self._items.remove(item)
        return item[2]

    def __len__(self):
        return len(self._items)
