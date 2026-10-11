class BoyerMooreSearch:
    def __init__(self, text, pattern):
        self.text, self.pattern = text, pattern
        self.textLen, self.patLen = len(text), len(pattern)

    def match_in_pattern(self, char):
        for i in range(self.patLen - 1, -1, -1):
            if self.pattern[i] == char:
                return i
        return -1

    def mismatch_in_text(self, currentPos):
        for i in range(self.patLen):
            if self.text[currentPos + i] != self.pattern[i]:
                return currentPos + i
        return -1

    def bad_character_heuristic(self):
        positions = []
        bad_char = [-1] * 256
        for i in range(self.patLen):
            bad_char[ord(self.pattern[i])] = i

        s = 0
        while s <= self.textLen - self.patLen:
            j = self.patLen - 1
            while j >= 0 and self.pattern[j] == self.text[s + j]:
                j -= 1
            if j < 0:
                positions.append(s)
                s += self.patLen - bad_char[ord(self.text[s + self.patLen])] if s + self.patLen < self.textLen else 1
            else:
                s += max(1, j - bad_char[ord(self.text[s + j])])
        return positions