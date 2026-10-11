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
            if x_idx == 0:
                x_idx = 1
            if y_idx == 0:
                y_idx = 1
            if x_idx == len(x):
                x_idx -= 1
            if y_idx == len(y):
                y_idx -= 1
            x_diff = x[x_idx] - x[x_idx - 1]
            y_diff = y[y_idx] - y[y_idx - 1]
            z_diff = z[x_idx, y_idx] - z[x_idx - 1, y_idx - 1]
            z_interp[i] = z[x_idx - 1, y_idx - 1] + (z_diff / x_diff) * (x_interp[i] - x[x_idx - 1]) + (z_diff / y_diff) * (y_interp[i] - y[y_idx - 1])
        return z_interp.tolist()

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

import unittest


class InterpolationTestInterpolate2d(unittest.TestCase):
    def test_interpolate_2d(self):
        interpolation = Interpolation()
        self.assertEqual(
            interpolation.interpolate_2d([1, 2, 3], [1, 2, 3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1.5, 2.5],
                                         [1.5, 2.5]), [3.0, 7.0])

    def test_interpolate_2d_2(self):
        interpolation = Interpolation()
        self.assertEqual(
            interpolation.interpolate_2d([1, 2, 3], [1, 2, 3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1.5, 2.5], [3, 4]),
            [4.5])

    def test_interpolate_2d_3(self):
        interpolation = Interpolation()
        self.assertEqual(
            interpolation.interpolate_2d([1, 2, 3], [1, 2, 3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [3, 4], [1.5, 2.5]),
            [7.5])

    def test_interpolate_2d_4(self):
        interpolation = Interpolation()
        self.assertEqual(
            interpolation.interpolate_2d([1, 2, 3], [1, 2, 3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [3, 4], [3, 4]),
            [9.0])

    def test_interpolate_2d_5(self):
        interpolation = Interpolation()
        self.assertEqual(
            interpolation.interpolate_2d([1, 2, 3], [1, 2, 3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1.5, 2.5],
                                         [1.5, 2.5]), [3.0, 7.0])


class InterpolationTestMain(unittest.TestCase):
    def test_main(self):
        interpolation = Interpolation()
        self.assertEqual(interpolation.interpolate_1d([1, 2, 3], [1, 2, 3], [1.5, 2.5]), [1.5, 2.5])
        self.assertEqual(
            interpolation.interpolate_2d([1, 2, 3], [1, 2, 3], [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1.5, 2.5],
                                         [1.5, 2.5]), [3.0, 7.0])

if __name__ == '__main__':
    unittest.main()
