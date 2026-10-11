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
                i = 0
                while x[i] < xi:
                    i += 1
                y_interp.append(y[i-1] + (y[i] - y[i-1]) * (xi - x[i-1]) / (x[i] - x[i-1]))
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
            if i > 0 and i < len(x) and j > 0 and j < len(y):
                z1 = z[i-1][j-1]
                z2 = z[i-1][j]
                z3 = z[i][j-1]
                z4 = z[i][j]
                dx1 = x[i] - x[i-1]
                dx2 = x[i] - xi
                dy1 = y[j] - y[j-1]
                dy2 = y[j] - yi
                z_interp = (z1 * dx2 * dy2 + z2 * dx1 * dy2 + z3 * dx2 * dy1 + z4 * dx1 * dy1) / (dx1 * dx2 * dy1 * dy2)
                result.append(z_interp)
            else:
                result.append(None)
        return result

import unittest


class InterpolationTestInterpolate1d(unittest.TestCase):
    def test_interpolate_1d(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([1, 2, 3], [1, 2, 3], [1.5, 2.5]), [1.5, 2.5])

    def test_interpolate_1d_2(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([1, 6, 4], [1, 2, 5], [1.5, 2.5]), [1.1, 1.3])

    def test_interpolate_1d_3(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([1, 6, 4], [1, 7, 5], [1.5, 2.5]), [1.6, 2.8])

    def test_interpolate_1d_4(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([1, 6, 4], [1, 2, 5], [2, 3]), [1.2, 1.4])

    def test_interpolate_1d_5(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([1, 6, 4], [1, 7, 5], [2, 3]), [2.2, 3.4])

    def test_interpolate_1d_6(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([1, 6, 4], [1, 7, 5], []), [])

    def test_interpolate_1d_7(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([], [], [[], []]), [])

if __name__ == '__main__':
    unittest.main()
