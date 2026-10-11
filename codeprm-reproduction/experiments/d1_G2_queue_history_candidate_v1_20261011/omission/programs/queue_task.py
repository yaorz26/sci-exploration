"""功能遗漏控制：与参考实现只差一处——对已在队列的任务再次 add 时，只更新优先级，
不把它移动到同优先级的新位置（即丢掉“更新即重排”的历史义务）。其余公开行为保持一致。
"""
import heapq


class PriorityQueue:
    def __init__(self):
        self._heap = []
        self._seq = 0
        self._live = {}

    def add(self, task, priority=None):
        priority = 0 if priority is None else priority
        if task in self._live:
            # 控制点：整条替换为“只改优先级、保持原有相对位置”的写法
            old_entry = self._live[task]
            self._live[task] = (-float(priority), old_entry[1])
            self._rebuild()
            return
        self._seq += 1
        entry = (-float(priority), self._seq)
        self._live[task] = entry
        heapq.heappush(self._heap, (entry[0], entry[1], task))

    def _rebuild(self):
        self._heap = [(-e[0], e[1], t) for t, e in self._live.items()]
        heapq.heapify(self._heap)

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
