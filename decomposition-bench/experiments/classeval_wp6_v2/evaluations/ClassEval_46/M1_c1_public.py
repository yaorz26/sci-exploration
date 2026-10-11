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
        y_interp = []
        for xi in x_interp:
            idx = bisect.bisect(x, xi)
            if idx == 0:
                y_interp.append(y[0])
            elif idx == len(x):
                y_interp.append(y[-1])
            else:
                x1, x2 = x[idx - 1], x[idx]
                y1, y2 = y[idx - 1], y[idx]
                y_interp.append(y1 + (xi - x1) * (y2 - y1) / (x2 - x1))
        return y_interp

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
        z_interp = []
        for xi, yi in zip(x_interp, y_interp):
            idx_x = bisect.bisect(x, xi)
            idx_y = bisect.bisect(y, yi)
            if idx_x == 0 or idx_y == 0 or idx_x == len(x) or idx_y == len(y):
                z_interp.append(z[0][0])
            else:
                x1, x2 = x[idx_x - 1], x[idx_x]
                y1, y2 = y[idx_y - 1], y[idx_y]
                z11, z12 = z[idx_y - 1][idx_x - 1], z[idx_y - 1][idx_x]
                z21, z22 = z[idx_y][idx_x - 1], z[idx_y][idx_x]
                z_interp.append((z11 * (x2 - xi) * (y2 - yi) +
                                z12 * (xi - x1) * (y2 - yi) +
                                z21 * (x2 - xi) * (yi - y1) +
                                z22 * (xi - x1) * (yi - y1)) /
                               ((x2 - x1) * (y2 - y1)))
        return z_interp

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
