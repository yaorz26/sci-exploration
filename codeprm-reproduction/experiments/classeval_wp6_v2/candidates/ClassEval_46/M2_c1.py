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
            if xi <= x[0]:
                y_interp.append(y[0])
            elif xi >= x[-1]:
                y_interp.append(y[-1])
            else:
                i = next(i for i, x_val in enumerate(x) if x_val > xi)
                y_interp.append(y[i - 1] + (y[i] - y[i - 1]) * (xi - x[i - 1]) / (x[i] - x[i - 1]))
        return y_interp

    def interpolate_2d(x, y, z, x_interp, y_interp):
        """
        Linear interpolation of two-dimensional data
        :param x: The x-coordinate of the data point, list.
        :param y: The y-coordinate of the data point, list.
        :param z: The z-coordinate of the data point, list.
        :param x_interp: The x-coordinate of the interpolation point, list.
        :param y_interp: The y-coordinate of the interpolation point, list.
        :return: The z-coordinate of the interpolation point, list.
        >>> interpolation = Interpolation()
        >>> interpolation.interpolate_2d([1, 2, 3], [1, 2, 3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1.5, 2.5], [1.5, 2.5])
        [3.0, 7.0]
        """
        result = []
        for xi, yi in zip(x_interp, y_interp):
            i = bisect.bisect_left(x, xi)
            j = bisect.bisect_left(y, yi)
            if i > 0 and i < len(x) - 1 and j > 0 and j < len(y) - 1:
                z1 = (z[i-1][j-1] * (x[i] - xi) * (y[j] - yi) +
                      z[i-1][j] * (x[i] - xi) * (yi - y[j-1]) +
                      z[i][j-1] * (xi - x[i-1]) * (y[j] - yi) +
                      z[i][j] * (xi - x[i-1]) * (yi - y[j-1])) / ((x[i] - x[i-1]) * (y[j] - y[j-1]))
                result.append(z1)
            else:
                result.append(None)
        return result
