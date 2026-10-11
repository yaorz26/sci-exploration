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
        >>> formatter = NumberWordFormatter()
        >>> formatter.format(123456)
        "ONE HUNDRED AND TWENTY THREE THOUSAND FOUR HUNDRED AND FIFTY SIX ONLY"
        """
        if isinstance(x, float):
            integer_part, decimal_part = str(x).split('.')
            integer_part = int(integer_part)
            decimal_part = int(decimal_part)
        else:
            integer_part = x
            decimal_part = 0

        result = []
        if integer_part == 0:
            result.append("ZERO")
        else:
            i = 0
            while integer_part > 0:
                group = integer_part % 1000
                if group > 0:
                    result.append(self.trans_three(str(group)) + " " + self.parse_more(i))
                integer_part //= 1000
                i += 1

        if decimal_part > 0:
            result.append("AND")
            for i in range(0, len(str(decimal_part)), 2):
                group = int(str(decimal_part)[i:i+2])
                if group > 0:
                    result.append(self.trans_two(str(group)) + " " + self.NUMBER_SUFFIX[i//2])

        result.append("ONLY")
        return " ".join(result).strip()

    def format_string(self, x):
        """
        Converts a string representation of a number into words format
        :param x: str, the string representation of a number
        :return: str, the number in words format
        >>> formatter = NumberWordFormatter()
        >>> formatter.format_string("123456")
        "ONE HUNDRED AND TWENTY THREE THOUSAND FOUR HUNDRED AND FIFTY SIX ONLY"
        """
        return self.format(int(x))

    def trans_two(self, s):
        """
        Converts a two-digit number into words format
        :param s: str, the two-digit number
        :return: str, the number in words format
        >>> formatter = NumberWordFormatter()
        >>> formatter.trans_two("23")
        "TWENTY THREE"
        """
        if int(s) < 10:
            return self.NUMBER[int(s)]
        elif 10 <= int(s) < 20:
            return self.NUMBER_TEEN[int(s) - 10]
        else:
            tens = int(s[0])
            ones = int(s[1])
            return self.NUMBER_TEN[tens - 1] + (" " + self.NUMBER[ones] if ones > 0 else "")

    def trans_three(self, s):
        """
        Converts a three-digit number into words format
        :param s: str, the three-digit number
        :return: str, the number in words format
        >>> formatter = NumberWordFormatter()
        >>> formatter.trans_three("123")
        "ONE HUNDRED AND TWENTY THREE"
        """
        hundreds = int(s[0])
        tens_ones = s[1:]
        if hundreds == 0:
            return self.trans_two(tens_ones)
        else:
            return self.NUMBER[hundreds] + " HUNDRED AND " + self.trans_two(tens_ones)

    def parse_more(self, i):
        """
        Parses the thousand/million/billion suffix based on the index
        :param i: int, the index representing the magnitude (thousand, million, billion)
        :return: str, the corresponding suffix for the magnitude
        >>> formatter = NumberWordFormatter()
        >>> formatter.parse_more(1)
        "THOUSAND"
        """
        if i == 0:
            return ""
        else:
            return self.NUMBER_MORE[i]

import unittest


class NumberWordFormatterTestFormat(unittest.TestCase):
    def test_format_1(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format(123456),
                         "ONE HUNDRED AND TWENTY THREE THOUSAND FOUR HUNDRED AND FIFTY SIX ONLY")

    def test_format_2(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format(1000), "ONE THOUSAND ONLY")

    def test_format_3(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format(1000000), "ONE MILLION ONLY")

    def test_format_4(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format(1.23), "ONE AND CENTS TWENTY THREE ONLY")

    def test_format_5(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format(0), "ZERO ONLY")

    def test_format_6(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format(None), "")


class NumberWordFormatterTestFormatString(unittest.TestCase):
    def test_format_string_1(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format_string('123456'),
                         "ONE HUNDRED AND TWENTY THREE THOUSAND FOUR HUNDRED AND FIFTY SIX ONLY")

    def test_format_string_2(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format_string('1000'), "ONE THOUSAND ONLY")

    def test_format_string_3(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format_string('1000000'), "ONE MILLION ONLY")

    def test_format_string_4(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format_string('1.23'), "ONE AND CENTS TWENTY THREE ONLY")

    def test_format_string_5(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format_string('0'), "ZERO ONLY")

    def test_format_string_6(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format_string('10'), "TEN ONLY")


class NumberWordFormatterTestTransTwo(unittest.TestCase):
    def test_trans_two_1(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_two("23"), "TWENTY THREE")

    def test_trans_two_2(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_two("10"), "TEN")

    def test_trans_two_3(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_two("05"), "FIVE")

    def test_trans_two_4(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_two("00"), "")

    def test_trans_two_5(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_two("01"), "ONE")

    def test_trans_two_6(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_two("80"), "EIGHTY")

import unittest


class NumberWordFormatterTestTransThree(unittest.TestCase):
    def test_trans_three_1(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_three("123"), "ONE HUNDRED AND TWENTY THREE")

    def test_trans_three_2(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_three("900"), "NINE HUNDRED")

    def test_trans_three_3(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_three("007"), "SEVEN")

    def test_trans_three_4(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_three("001"), "ONE")

    def test_trans_three_5(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_three("006"), "SIX")


class NumberWordFormatterTestParseMore(unittest.TestCase):
    def test_parse_more_1(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.parse_more(0), "")

    def test_parse_more_2(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.parse_more(1), "THOUSAND")

    def test_parse_more_3(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.parse_more(2), "MILLION")

    def test_parse_more_4(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.parse_more(3), "BILLION")


class NumberWordFormatterTest(unittest.TestCase):
    def test_NumberWordFormatter(self):
        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format(123456),
                         "ONE HUNDRED AND TWENTY THREE THOUSAND FOUR HUNDRED AND FIFTY SIX ONLY")

        formatter = NumberWordFormatter()
        self.assertEqual(formatter.format_string('123456'),
                         "ONE HUNDRED AND TWENTY THREE THOUSAND FOUR HUNDRED AND FIFTY SIX ONLY")

        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_two("23"), "TWENTY THREE")

        formatter = NumberWordFormatter()
        self.assertEqual(formatter.trans_three("123"), "ONE HUNDRED AND TWENTY THREE")

        formatter = NumberWordFormatter()
        self.assertEqual(formatter.parse_more(1), "THOUSAND")

if __name__ == '__main__':
    unittest.main()
