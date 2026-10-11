class NumberWordFormatter:
    """
    This is a class that provides to convert numbers into their corresponding English word representation, including handling the conversion of both the integer and decimal parts, and incorporating appropriate connectors and units.
    """

    def __init__(self):
        """
        Initialize NumberWordFormatter object.
        """
        self.NUMBER = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]
        self.NUMBER_TEEN = ["TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN",
                            "EIGHTEEN",
                            "NINETEEN"]
        self.NUMBER_TEN = ["TEN", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]
        self.NUMBER_MORE = ["", "THOUSAND", "MILLION", "BILLION"]
        self.NUMBER_SUFFIX = ["k", "w", "", "m", "", "", "b", "", "", "t", "", "", "p", "", "", "e"]

    def format(self, x):
        """
        Converts a number into words format
        :param x: int or float, the number to be converted into words format
        :return: str, the number in words format
        """
        if isinstance(x, float):
            integer_part, decimal_part = str(x).split('.')
            integer_words = self.format_string(integer_part)
            decimal_words = self.format_string(decimal_part)
            return f"{integer_words} POINT {decimal_words}"
        else:
            return self.format_string(str(x))

    def format_string(self, x):
        """
        Converts a string representation of a number into words format
        :param x: str, the string representation of a number
        :return: str, the number in words format
        """
        if len(x) == 1:
            return self.NUMBER[int(x)]
        elif len(x) == 2:
            return self.trans_two(x)
        elif len(x) == 3:
            return self.trans_three(x)
        else:
            result = []
            i = 0
            while i < len(x):
                chunk = x[i:i+3]
                if chunk == '000':
                    i += 3
                else:
                    result.append(self.trans_three(chunk))
                    result.append(self.parse_more(len(x) - i - 3))
                    i += 3
            return ' '.join(filter(None, result))

    def trans_two(self, s):
        """
        Converts a two-digit number into words format
        :param s: str, the two-digit number
        :return: str, the number in words format
        """
        if s[0] == '0':
            return self.NUMBER[int(s[1])]
        elif s[0] == '1':
            return self.NUMBER_TEEN[int(s[1])]
        else:
            result = [self.NUMBER_TEN[int(s[0])]]
            if s[1] != '0':
                result.append(self.NUMBER[int(s[1])])
            return ' '.join(result)

    def trans_three(self, s):
        """
        Converts a three-digit number into words format
        :param s: str, the three-digit number
        :return: str, the number in words format
        """
        if s[0] == '0':
            return self.trans_two(s[1:])
        else:
            return f"{self.NUMBER[int(s[0])] }HUNDRED AND {self.trans_two(s[1:])}"

    def parse_more(self, i):
        """
        Parses the thousand/million/billion suffix based on the index
        :param i: int, the index representing the magnitude (thousand, million, billion)
        :return: str, the corresponding suffix for the magnitude
        """
        if i == 0:
            return ""
        else:
            return self.NUMBER_MORE[i]