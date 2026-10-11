class AvgPartition:
    """
    This is a class that partitions the given list into different blocks by specifying the number of partitions, with each block having a uniformly distributed length.
    """

    def __init__(self, lst, limit):
        """
        Initialize the class with the given list and the number of partitions, and check if the number of partitions is greater than 0.
        """
        if limit <= 0:
            raise ValueError("The number of partitions must be greater than 0.")
        self.lst = lst
        self.limit = limit

    def setNum(self):
        """
        Calculate the size of each block and the remainder of the division.
        :return: the size of each block and the remainder of the division, tuple.
        """
        length = len(self.lst)
        quotient, remainder = divmod(length, self.limit)
        return quotient, remainder

    def get(self, index):
        """
        Calculate the size of each block and the remainder of the division, and calculate the corresponding start and end positions based on the index of the partition.
        :param index: the index of the partition, int.
        :return: the corresponding block, list.
        """
        quotient, remainder = self.setNum()
        if index < remainder:
            block_size = quotient + 1
            start = index * block_size
        else:
            block_size = quotient
            start = remainder * (quotient + 1) + (index - remainder) * block_size
        end = start + block_size
        return self.lst[start:end]