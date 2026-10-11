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
        self.processed_string = '#' + '#'.join(input_string) + '#'
        self.radius = [0] * len(self.processed_string)

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
        max_radius = 0
        max_center = 0
        for i in range(len(self.processed_string)):
            if i < max_center + max_radius:
                self.radius[i] = min(max_radius - (i - max_center), self.radius[2 * max_center - i])
            self.radius[i] = self.palindromic_length(i, self.radius[i], self.processed_string)
            if i + self.radius[i] > max_center + max_radius:
                max_center = i
                max_radius = self.radius[i]
        start = (max_center - max_radius) // 2
        return self.input_string[start:start + max_radius]