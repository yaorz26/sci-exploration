class Manacher:
    """
    his is a class that implements a manacher algorithm to find the Longest palindromic substring in a given string.
    """

    def __init__(self, input_string) -> None:
        """
        Initializes the Manacher class with the given input_string.
        :param input_string: The input_string to be searched, str.
        """
        self.input_string = input_string

    def palindromic_length(self, center, diff, string):
        """
        Recursively calculates the length of the palindromic substring based on a given center, difference value, and input string.
        :param center: The center of the palindromic substring, int.
        :param diff: The difference between the center and the current position, int.
        :param string: The string to be searched, str.
        :return: The length of the palindromic substring, int.
        """
        while center - diff >= 0 and center + diff < len(string) and string[center - diff] == string[center + diff]:
            diff += 1
        return diff - 1

    def palindromic_string(self):
        """
        Finds the longest palindromic substring in the given string.
        :return: The longest palindromic substring, str.
        >>> manacher = Manacher('ababaxse')
        >>> manacher.palindromic_string()
        'ababa'
        """
        input_string = self.input_string
        n = len(input_string)
        if n == 0:
            return ""

        # Transform the string to handle even length palindromes
        transformed_string = '#'.join('^{}$'.format(input_string))
        n = len(transformed_string)
        p = [0] * n
        center = right = 0

        for i in range(1, n-1):
            if i < right:
                p[i] = min(right - i, p[2 * center - i])

            # Attempt to expand palindrome centered at i
            while transformed_string[i + 1 + p[i]] == transformed_string[i - 1 - p[i]]:
                p[i] += 1

            # If palindrome centered at i expands past right, adjust center and right
            if i + p[i] > right:
                center = i
                right = i + p[i]

        # Find the maximum element in p
        max_len = max(p)
        center_index = p.index(max_len)
        start_index = (center_index - max_len) // 2
        return input_string[start_index:start_index + max_len]

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

if __name__ == '__main__':
    unittest.main()
