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
