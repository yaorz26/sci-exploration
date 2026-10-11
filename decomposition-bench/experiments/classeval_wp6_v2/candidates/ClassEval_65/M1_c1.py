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
            integer_words = self.trans_three(integer_part)
            decimal_words = self.trans_two(decimal_part)
            return f"{integer_words} POINT {decimal_words} ONLY"
        else:
            return self.trans_three(str(x)) + " ONLY"

    def format_string(self, x):
        """
        Converts a string representation of a number into words format
        :param x: str, the string representation of a number
        :return: str, the number in words format
        """
        return self.format(int(x))

    def trans_two(self, s):
        """
        Converts a two-digit number into words format
        :param s: str, the two-digit number
        :return: str, the number in words format
        """
        if int(s) < 20:
            return self.NUMBER_TEEN[int(s) - 10]
        else:
            tens = self.NUMBER_TEN[int(s[0]) - 1]
            ones = self.NUMBER[int(s[1])]
            if ones:
                return f"{tens} {ones}"
            else:
                return tens

    def trans_three(self, s):
        """
        Converts a three-digit number into words format
        :param s: str, the three-digit number
        :return: str, the number in words format
        """
        hundreds = self.NUMBER[int(s[0])]
        tens_ones = self.trans_two(s[1:])
        if hundreds and tens_ones:
            return f"{hundreds} HUNDRED AND {tens_ones}"
        elif hundreds:
            return f"{hundreds} HUNDRED"
        else:
            return tens_ones

    def parse_more(self, i):
        """
        Parses the thousand/million/billion suffix based on the index
        :param i: int, the index representing the magnitude (thousand, million, billion)
        :return: str, the corresponding suffix for the magnitude
        """
        return self.NUMBER_MORE[i]