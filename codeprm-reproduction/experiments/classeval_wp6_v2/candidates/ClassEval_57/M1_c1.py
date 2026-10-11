import numpy as np


class MetricsCalculator2:
    """
    The class provides to calculate Mean Reciprocal Rank (MRR) and Mean Average Precision (MAP) based on input data, where MRR measures the ranking quality and MAP measures the average precision.
    """

    def __init__(self):
        pass

    @staticmethod
    def mrr(data):
        """
        compute the MRR of the input data. MRR is a widely used evaluation index. It is the mean of reciprocal rank.
        :param data: the data must be a tuple, list 0,1,eg.([1,0,...],5).  In each tuple (actual result,ground truth num),ground truth num is the total ground num.
         ([1,0,...],5),
        or list of tuple eg. [([1,0,1,...],5),([1,0,...],6),([0,0,...],5)].
        1 stands for a correct answer, 0 stands for a wrong answer.
        :return: if input data is list, return the recall of this list. if the input data is list of list, return the
        average recall on all list. The second return value is a list of precision for each input.
        >>> MetricsCalculator2.mrr(([1, 0, 1, 0], 4))
        >>> MetricsCalculator2.mrr([([1, 0, 1, 0], 4), ([0, 1, 0, 1], 4)])
        1.0, [1.0]
        0.75, [1.0, 0.5]
        """
        if isinstance(data, list):
            total_mrr = 0
            mrr_list = []
            for item in data:
                total_mrr += MetricsCalculator2._mrr_single(item)
                mrr_list.append(MetricsCalculator2._mrr_single(item))
            average_mrr = total_mrr / len(data)
            return average_mrr, mrr_list
        else:
            return MetricsCalculator2._mrr_single(data)

    @staticmethod
    def _mrr_single(item):
        actual_result, ground_truth_num = item
        rank = 0
        for i, result in enumerate(actual_result):
            if result == 1:
                rank = i + 1
                break
        if rank == 0:
            return 0
        return 1 / rank

    @staticmethod
    def map(data):
        """
        compute the MAP of the input data. MAP is a widely used evaluation index. It is the mean of AP (average precision).
        :param data: the data must be a tuple, list 0,1,eg.([1,0,...],5).  In each tuple (actual result,ground truth num),ground truth num is the total ground num.
         ([1,0,...],5),
        or list of tuple eg. [([1,0,1,...],5),([1,0,...],6),([0,0,...],5)].
        1 stands for a correct answer, 0 stands for a wrong answer.
        :return: if input data is list, return the recall of this list. if the input data is list of list, return the
        average recall on all list. The second return value is a list of precision for each input.
        >>> MetricsCalculator2.map(([1, 0, 1, 0], 4))
        >>> MetricsCalculator2.map([([1, 0, 1, 0], 4), ([0, 1, 0, 1], 4)])
        0.41666666666666663, [0.41666666666666663]
        0.3333333333333333, [0.41666666666666663, 0.25]
        """
        if isinstance(data, list):
            total_map = 0
            map_list = []
            for item in data:
                total_map += MetricsCalculator2._map_single(item)
                map_list.append(MetricsCalculator2._map_single(item))
            average_map = total_map / len(data)
            return average_map, map_list
        else:
            return MetricsCalculator2._map_single(data)

    @staticmethod
    def _map_single(item):
        actual_result, ground_truth_num = item
        precision_sum = 0
        relevant_count = 0
        for i, result in enumerate(actual_result):
            if result == 1:
                relevant_count += 1
                precision_sum += relevant_count / (i + 1)
        if relevant_count == 0:
            return 0
        return precision_sum / relevant_count