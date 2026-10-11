class BalancedBrackets:
    def __init__(self, expr):
        self.stack = []
        self.left_brackets = ["(", "{", "["]
        self.right_brackets = [")", "}", "]"]
        self.expr = expr

    def clear_expr(self):
        self.expr = ''.join(c for c in self.expr if (c in self.left_brackets or c in self.right_brackets))

    def check_balanced_brackets(self):
        self.clear_expr()
        for Brkt in self.expr:
            if Brkt in self.left_brackets:
                self.stack.append(Brkt)
            else:
                Current_Brkt = self.stack.pop()
                if Current_Brkt == "(":
                    if Brkt != ")":
                        return False
                if Current_Brkt == "{":
                    if Brkt != "}":
                        return False
                if Current_Brkt == "[":
                    if Brkt != "]":
                        return False
        if self.stack:
            return False
        return True

import unittest


class BalancedBracketsTestClearExpr(unittest.TestCase):
    def test_clear_expr(self):
        b = BalancedBrackets("a(b)c")
        b.clear_expr()
        self.assertEqual(b.expr, "()")

    def test_clear_expr_2(self):
        b = BalancedBrackets("a(b){c}")
        b.clear_expr()
        self.assertEqual(b.expr, "(){}")

    def test_clear_expr_3(self):
        b = BalancedBrackets("[a](b){c}")
        b.clear_expr()
        self.assertEqual(b.expr, "[](){}")

    def test_clear_expr_4(self):
        b = BalancedBrackets("[a(b){c}")
        b.clear_expr()
        self.assertEqual(b.expr, "[(){}")

    def test_clear_expr_5(self):
        b = BalancedBrackets("a(b){c}]")
        b.clear_expr()
        self.assertEqual(b.expr, "(){}]")

import unittest


class BalancedBracketsTestCheckBalancedBrackets(unittest.TestCase):
    def test_check_balanced_brackets(self):
        b = BalancedBrackets("a(b)c")
        self.assertEqual(b.check_balanced_brackets(), True)

    def test_check_balanced_brackets_2(self):
        b = BalancedBrackets("a(b){c}")
        self.assertEqual(b.check_balanced_brackets(), True)

    def test_check_balanced_brackets_3(self):
        b = BalancedBrackets("[a](b){c}")
        self.assertEqual(b.check_balanced_brackets(), True)

    def test_check_balanced_brackets_4(self):
        b = BalancedBrackets("[a(b){c}")
        self.assertEqual(b.check_balanced_brackets(), False)

    def test_check_balanced_brackets_5(self):
        b = BalancedBrackets("a(b{c}]")
        self.assertEqual(b.check_balanced_brackets(), False)

    def test_check_balanced_brackets_6(self):
        b = BalancedBrackets("a(b{c]]")
        self.assertEqual(b.check_balanced_brackets(), False)

    def test_check_balanced_brackets_7(self):
        b = BalancedBrackets("[a)(b){c}")
        self.assertEqual(b.check_balanced_brackets(), False)


class BalancedBracketsTestMain(unittest.TestCase):
    def test_main(self):
        b = BalancedBrackets("a(b)c")
        b.clear_expr()
        self.assertEqual(b.expr, "()")
        self.assertEqual(b.check_balanced_brackets(), True)

    def test_main_2(self):
        b = BalancedBrackets("[a(b){c}")
        b.clear_expr()
        self.assertEqual(b.expr, "[(){}")
        self.assertEqual(b.check_balanced_brackets(), False)

    def test_main_3(self):
        b = BalancedBrackets("a(b{c}]")
        b.clear_expr()
        self.assertEqual(b.expr, "({}]")
        self.assertEqual(b.check_balanced_brackets(), False)

if __name__ == '__main__':
    unittest.main()
