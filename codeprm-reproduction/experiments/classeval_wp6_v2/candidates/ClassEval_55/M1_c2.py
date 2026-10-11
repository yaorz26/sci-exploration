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

    def palindromic_length(self, center, diff, string):
        """
        Recursively calculates the length of the palindromic substring based on a given center, difference value, and input string.
        :param center: The center of the palindromic substring, int.
        :param diff: The difference between the center and the current position, int.
        :param string: The string to be searched, str.
        :return: The length of the palindromic substring, int.
        """
        if center - diff < 0 or center + diff >= len(string) or string[center - diff] != string[center + diff]:
            return 0
        return 2 + self.palindromic_length(center, diff + 1, string)

    def palindromic_string(self):
        """
        Finds the longest palindromic substring in the given string.
        :return: The longest palindromic substring, str.
        """
        if not self.input_string:
            return ""

        # Transform the input string to handle both even and odd length palindromes
        transformed_string = '#'.join('^{}$'.format(self.input_string))
        n = len(transformed_string)
        p = [0] * n
        center = right = 0

        for i in range(1, n - 1):
            mirror = 2 * center - i
            if i < right:
                p[i] = min(right - i, p[mirror])

            # Attempt to expand palindrome centered at i
            while transformed_string[i + 1 + p[i]] == transformed_string[i - 1 - p[i]]:
                p[i] += 1

            # Update center and right if the palindrome centered at i expands past right
            if i + p[i] > right:
                center = i
                right = i + p[i]

        # Find the maximum length and its center
        max_len = max(p)
        max_center = p.index(max_len)

        # Extract the longest palindromic substring
        start = (max_center - max_len) // 2
        return self.input_string[start:start + max_len]