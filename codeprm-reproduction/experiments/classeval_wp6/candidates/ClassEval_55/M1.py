class Manacher:
    def __init__(self, input_string) -> None:
        self.input_string = '#' + '#'.join(input_string) + '#'
        self.P = [0] * len(self.input_string)
        self.C = 0
        self.R = 0

    def palindromic_length(self, center, diff, string):
        while center - diff >= 0 and center + diff < len(string) and string[center - diff] == string[center + diff]:
            diff += 1
        return diff - 1

    def palindromic_string(self):
        for i in range(1, len(self.input_string) - 1):
            if i < self.R:
                mirror = 2 * self.C - i
                self.P[i] = min(self.R - i, self.P[mirror])
            self.P[i] = self.palindromic_length(i, self.P[i], self.input_string)
            if i + self.P[i] > self.R:
                self.C = i
                self.R = i + self.P[i]
        max_len = max(self.P)
        max_index = self.P.index(max_len)
        return self.input_string[max_index - max_len:max_index + max_len + 1].replace('#', '')