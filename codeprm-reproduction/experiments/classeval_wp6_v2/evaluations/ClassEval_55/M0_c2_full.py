class Manacher:
    """
    This is a class that implements a manacher algorithm to find the Longest palindromic substring in a given string.
    """

    def __init__(self, input_string) -> None:
        """
        Initializes the Manacher class with the given input_string.
        :param input_string: The input_string to be searched, str.
        """
        self.input_string = input_string
        self.transformed_string = '#' + '#'.join(input_string) + '#'
        self.palindrome_lengths = [0] * len(self.transformed_string)
        self.center = 0
        self.right = 0

    def expand_around_center(self, center):
        """
        Expands around the center to find the palindrome length.
        :param center: The center of the palindromic substring, int.
        """
        while center - self.palindrome_lengths[center] - 1 >= 0 and center + self.palindrome_lengths[center] + 1 < len(self.transformed_string) and self.transformed_string[center - self.palindrome_lengths[center] - 1] == self.transformed_string[center + self.palindrome_lengths[center] + 1]:
            self.palindrome_lengths[center] += 1

    def palindromic_string(self):
        """
        Finds the longest palindromic substring in the given string.
        :return: The longest palindromic substring, str.
        """
        for i in range(1, len(self.transformed_string) - 1):
            if i < self.right:
                mirror = 2 * self.center - i
                self.palindrome_lengths[i] = min(self.right - i, self.palindrome_lengths[mirror])
            self.expand_around_center(i)
            if i + self.palindrome_lengths[i] > self.right:
                self.center = i
                self.right = i + self.palindrome_lengths[i]

        max_length = max(self.palindrome_lengths)
        center_index = self.palindrome_lengths.index(max_length)
        start_index = (center_index - max_length) // 2
        return self.input_string[start_index:start_index + max_length]

import unittest

class ManacherTestPalindromicLength(unittest.TestCase):
    def test_palindromic_length(self):
        manacher = Manacher('ababa')
        self.assertEqual(manacher.palindromic_length(2, 1, 'a|b|a|b|a'), 2)
    def test_palindromic_length_2(self):
        manacher = Manacher('ababaxse')
        self.assertEqual(manacher.palindromic_length(2, 1, 'a|b|a|b|a|x|s|e'), 2)

    def test_palindromic_length_3(self):
        manacher = Manacher('ababax')
        self.assertEqual(manacher.palindromic_length(2, 3, 'a|b|a|b|a|x'), 0)

    def test_palindromic_length_4(self):
        manacher = Manacher('ababax')
        self.assertEqual(manacher.palindromic_length(9, 2, 'a|b|a|b|a|x'), 0)

    def test_palindromic_length_5(self):
        manacher = Manacher('ababax')
        self.assertEqual(manacher.palindromic_length(4, 1, 'a|b|a|b|a|x'), 4)

import unittest

class ManacherTestPalindromicString(unittest.TestCase):
    def test_palindromic_string(self):
        manacher = Manacher('ababaxse')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_2(self):
        manacher = Manacher('ababax')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_3(self):
        manacher = Manacher('ababax')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_4(self):
        manacher = Manacher('ababaxssss')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_5(self):
        manacher = Manacher('abab')
        self.assertEqual(manacher.palindromic_string(), 'aba')


class ManacherTestMain(unittest.TestCase):
    def test_main(self):
        manacher = Manacher('ababa')
        self.assertEqual(manacher.palindromic_length(2, 1, 'a|b|a|b|a'), 2)
        self.assertEqual(manacher.palindromic_string(), 'ababa')

if __name__ == '__main__':
    unittest.main()
