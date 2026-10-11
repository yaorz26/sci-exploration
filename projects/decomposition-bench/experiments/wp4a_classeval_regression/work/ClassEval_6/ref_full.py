class AvgPartition:
    def __init__(self, lst, limit):
        self.lst = lst
        self.limit = limit

    def setNum(self):
        size = len(self.lst) // self.limit
        remainder = len(self.lst) % self.limit
        return size, remainder

        
    def get(self, index):
        size, remainder = self.setNum()
        start = index * size + min(index, remainder)
        end = start + size
        if index + 1 <= remainder:
            end += 1
        return self.lst[start:end]

import unittest

class AvgPartitionTestSetNum(unittest.TestCase):
    def test_setNum(self):
        a = AvgPartition([1, 2, 3, 4], 2)
        self.assertEqual(a.setNum(), (2, 0))

    def test_setNum_2(self):
        a = AvgPartition([1, 2, 3, 4, 5], 2)
        self.assertEqual(a.setNum(), (2, 1))

    def test_setNum_3(self):
        a = AvgPartition([1, 2, 3, 4, 5], 3)
        self.assertEqual(a.setNum(), (1, 2))

    def test_setNum_4(self):
        a = AvgPartition([1, 2, 3, 4, 5], 4)
        self.assertEqual(a.setNum(), (1, 1))

    def test_setNum_5(self):
        a = AvgPartition([1, 2, 3, 4, 5], 5)
        self.assertEqual(a.setNum(), (1, 0))

class AvgPartitionTestGet(unittest.TestCase):

    def test_get(self):
        a = AvgPartition([1, 2, 3, 4], 2)
        self.assertEqual(a.get(0), [1, 2])

    def test_get_2(self):
        a = AvgPartition([1, 2, 3, 4], 2)
        self.assertEqual(a.get(1), [3, 4])

    def test_get_3(self):
        a = AvgPartition([1, 2, 3, 4, 5], 2)
        self.assertEqual(a.get(0), [1, 2, 3])

    def test_get_4(self):
        a = AvgPartition([1, 2, 3, 4, 5], 2)
        self.assertEqual(a.get(1), [4, 5])

    def test_get_5(self):
        a = AvgPartition([1, 2, 3, 4, 5], 3)
        self.assertEqual(a.get(0), [1, 2])

class AvgPartitionTestMain(unittest.TestCase):
    def test_main(self):
        a = AvgPartition([1, 2, 3, 4], 2)
        self.assertEqual(a.setNum(), (2, 0))
        self.assertEqual(a.get(0), [1, 2])

if __name__ == '__main__':
    unittest.main()
