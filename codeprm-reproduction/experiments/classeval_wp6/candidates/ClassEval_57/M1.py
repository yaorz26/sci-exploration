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
            mrr_values = []
            for sample in data:
                actual_result, ground_truth_num = sample
                rank = next((i + 1 for i, x in enumerate(actual_result) if x == 1), None)
                if rank is not None:
                    mrr_values.append(1 / rank)
                else:
                    mrr_values.append(0)
            return np.mean(mrr_values), mrr_values
        else:
            actual_result, ground_truth_num = data
            rank = next((i + 1 for i, x in enumerate(actual_result) if x == 1), None)
            if rank is not None:
                return 1 / rank, [1 / rank]
            else:
                return 0, [0]

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
            map_values = []
            for sample in data:
                actual_result, ground_truth_num = sample
                precision_values = []
                correct_count = 0
                for i, x in enumerate(actual_result):
                    if x == 1:
                        correct_count += 1
                        precision_values.append(correct_count / (i + 1))
                ap = sum(precision_values) / ground_truth_num if ground_truth_num > 0 else 0
                map_values.append(ap)
            return np.mean(map_values), map_values
        else:
            actual_result, ground_truth_num = data
            precision_values = []
            correct_count = 0
            for i, x in enumerate(actual_result):
                if x == 1:
                    correct_count += 1
                    precision_values.append(correct_count / (i + 1))
            ap = sum(precision_values) / ground_truth_num if ground_truth_num > 0 else 0
            return ap, [ap]