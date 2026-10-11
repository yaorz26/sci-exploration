import numpy as np

class DataStatistics2:
    """
    This is a class for performing data statistics, supporting to get the sum, minimum, maximum, variance, standard deviation, and correlation of a given dataset.
    """

    def __init__(self, data):
        """
        Initialize Data List
        :param data:list
        """
        self.data = np.array(data)

    def get_sum(self):
        """
        Calculate the sum of data
        :return:float
        """
        return np.sum(self.data)

    def get_min(self):
        """
        Calculate the minimum value in the data
        :return:float
        """
        return np.min(self.data)

    def get_max(self):
        """
        Calculate the maximum value in the data
        :return:float
        """
        return np.max(self.data)

    def get_variance(self):
        """
        Calculate variance, accurate to two digits after the Decimal separator
        :return:float
        """
        variance = np.var(self.data)
        return round(variance, 2)

    def get_std_deviation(self):
        """
        Calculate standard deviation, accurate to two digits after the Decimal separator
        :return:float
        """
        std_deviation = np.std(self.data)
        return round(std_deviation, 2)

    def get_correlation(self):
        """
        Calculate correlation
        :return:float
        """
        correlation_matrix = np.corrcoef(self.data, self.data)
        return correlation_matrix[0, 1]