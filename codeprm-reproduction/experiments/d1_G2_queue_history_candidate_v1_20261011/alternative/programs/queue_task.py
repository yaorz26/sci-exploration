"""另一种合法组织：用 heapq 维护最小堆，条目为 (neg_priority, seq, uid)，另用字典做任务到条目的映射。

约定与参考实现相同：数值越大越先出队；同优先级先入先出；再次 add 视为更新并按新序号重排。
本实现不使用排序列表，靠堆与懒删除实现同样的公开行为。
"""
import heapq


class PriorityQueue:
    def __init__(self):
        self._heap = []
        self._seq = 0
        self._live = {}           # task -> (neg_priority, seq)

    def add(self, task, priority=None):
        priority = 0 if priority is None else priority
        if task in self._live:
            del self._live[task]          # 懒删除：旧条目留在堆里，由 _cull 清理
        self._seq += 1
        entry = (-float(priority), self._seq)
        self._live[task] = entry
        heapq.heappush(self._heap, (entry[0], entry[1], task))

    def _cull(self):
        while self._heap:
            neg_p, seq, task = self._heap[0]
            if task in self._live and self._live[task] == (neg_p, seq):
                return
            heapq.heappop(self._heap)

    def remove(self, task):
        if task not in self._live:
            raise KeyError(task)
        del self._live[task]

    def peek(self, default=None):
        self._cull()
        if not self._heap:
            if default is None:
                raise IndexError('peek on empty queue')
            return default
        return self._heap[0][2]

    def pop(self, default=None):
        self._cull()
        if not self._heap:
            if default is None:
                raise IndexError('pop on empty queue')
            return default
        _, _, task = heapq.heappop(self._heap)
        del self._live[task]
        return task

    def __len__(self):
        return len(self._live)
