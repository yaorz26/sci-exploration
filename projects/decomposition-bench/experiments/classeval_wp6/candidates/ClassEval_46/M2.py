class Interpolation:
    """
    This is a class that implements the Linear interpolation operation of one-dimensional and two-dimensional data
    """

    def __init__(self):
        pass

    @staticmethod
    def interpolate_1d(x, y, x_interp):
        """
        Linear interpolation of one-dimensional data
        :param x: The x-coordinate of the data point, list.
        :param y: The y-coordinate of the data point, list.
        :param x_interp: The x-coordinate of the interpolation point, list.
        :return: The y-coordinate of the interpolation point, list.
        >>> interpolation = Interpolation()
        >>> interpolation.interpolate_1d([1, 2, 3], [1, 2, 3], [1.5, 2.5])
        [1.5, 2.5]
        """
        y_interp = []
        for xi in x_interp:
            idx = bisect.bisect_left(x, xi)
            if idx == 0:
                y_interp.append(y[0])
            elif idx == len(x):
                y_interp.append(y[-1])
            else:
                x1, x2 = x[idx-1], x[idx]
                y1, y2 = y[idx-1], y[idx]
                y_interp.append(y1 + (xi - x1) * (y2 - y1) / (x2 - x1))
        return y_interp