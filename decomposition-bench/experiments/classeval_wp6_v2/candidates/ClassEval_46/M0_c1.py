import numpy as np

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
        """
        x = np.array(x)
        y = np.array(y)
        x_interp = np.array(x_interp)
        y_interp = np.interp(x_interp, x, y)
        return y_interp.tolist()

    @staticmethod
    def interpolate_2d(x, y, z, x_interp, y_interp):
        """
        Linear interpolation of two-dimensional data
        :param x: The x-coordinate of the data point, list.
        :param y: The y-coordinate of the data point, list.
        :param z: The z-coordinate of the data point, list.
        :param x_interp: The x-coordinate of the interpolation point, list.
        :param y_interp: The y-coordinate of the interpolation point, list.
        :return: The z-coordinate of the interpolation point, list.
        """
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)
        x_interp = np.array(x_interp)
        y_interp = np.array(y_interp)
        z_interp = np.zeros_like(x_interp)
        for i in range(len(x_interp)):
            x_idx = np.searchsorted(x, x_interp[i])
            y_idx = np.searchsorted(y, y_interp[i])
            if x_idx == 0 or y_idx == 0:
                z_interp[i] = z[0, 0]
            elif x_idx == len(x) or y_idx == len(y):
                z_interp[i] = z[-1, -1]
            else:
                z_interp[i] = (z[x_idx-1, y_idx-1] * (x[x_idx] - x_interp[i]) * (y[y_idx] - y_interp[i]) +
                              z[x_idx, y_idx-1] * (x_interp[i] - x[x_idx-1]) * (y[y_idx] - y_interp[i]) +
                              z[x_idx-1, y_idx] * (x[x_idx] - x_interp[i]) * (y_interp[i] - y[y_idx-1]) +
                              z[x_idx, y_idx] * (x_interp[i] - x[x_idx-1]) * (y_interp[i] - y[y_idx-1])) / \
                             ((x[x_idx] - x[x_idx-1]) * (y[y_idx] - y[y_idx-1]))
        return z_interp.tolist()