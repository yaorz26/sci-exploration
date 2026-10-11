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
        self.transformed_string = self._transform_string(input_string)

    def _transform_string(self, string):
        """
        Transforms the input string to a format suitable for the Manacher algorithm.
        :param string: The input string, str.
        :return: The transformed string, str.
        """
        return '#' + '#'.join(string) + '#'

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
        """
        p = [0] * len(self.transformed_string)
        center = right = 0
        max_len = 0
        max_center = 0

        for i in range(1, len(self.transformed_string) - 1):
            if i < right:
                p[i] = min(right - i, p[2 * center - i])

            while self.transformed_string[i + p[i] + 1] == self.transformed_string[i - p[i] - 1]:
                p[i] += 1

            if i + p[i] > right:
                center = i
                right = i + p[i]

            if p[i] > max_len:
                max_len = p[i]
                max_center = i

        start = (max_center - max_len) // 2
        return self.input_string[start:start + max_len]