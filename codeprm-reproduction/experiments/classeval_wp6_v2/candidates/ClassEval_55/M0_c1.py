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
        self.palindrome_lengths = [0] * len(self.transformed_string)
        self.center = 0
        self.right = 0

    def _transform_string(self, s):
        """
        Transforms the input string to include special characters to handle even-length palindromes.
        :param s: The input string, str.
        :return: The transformed string, str.
        """
        return '#' + '#'.join(s) + '#'

    def palindromic_string(self):
        """
        Finds the longest palindromic substring in the given string.
        :return: The longest palindromic substring, str.
        """
        for i in range(1, len(self.transformed_string) - 1):
            mirror = 2 * self.center - i
            if i < self.right:
                self.palindrome_lengths[i] = min(self.right - i, self.palindrome_lengths[mirror])

            while self.transformed_string[i + self.palindrome_lengths[i] + 1] == self.transformed_string[i - self.palindrome_lengths[i] - 1]:
                self.palindrome_lengths[i] += 1

            if i + self.palindrome_lengths[i] > self.right:
                self.center = i
                self.right = i + self.palindrome_lengths[i]

        max_length = max(self.palindrome_lengths)
        max_index = self.palindrome_lengths.index(max_length)
        return self.input_string[(max_index - max_length) // 2:(max_index + max_length) // 2]