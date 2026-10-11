class Calculator:
    def __init__(self):
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y
        }

    def calculate(self, expression):
        operand_stack = []
        operator_stack = []
        num_buffer = ''

        for char in expression:
            if char.isdigit() or char == '.':
                num_buffer += char
            else:
                if num_buffer:
                    operand_stack.append(float(num_buffer))
                    num_buffer = ''

                if char in '+-*/^':
                    while (
                            operator_stack and
                            operator_stack[-1] != '(' and
                            self.precedence(operator_stack[-1]) >= self.precedence(char)
                    ):
                        operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

                    operator_stack.append(char)
                elif char == '(':
                    operator_stack.append(char)
                elif char == ')':
                    while operator_stack and operator_stack[-1] != '(':
                        operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

                    operator_stack.pop()

        if num_buffer:
            operand_stack.append(float(num_buffer))

        while operator_stack:
            operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

        return operand_stack[-1] if operand_stack else None

    def precedence(self, operator):
        precedences = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            '^': 3
        }
        return precedences.get(operator, 0)

    def apply_operator(self, operand_stack, operator_stack):
        operator = operator_stack.pop()
        if operator == '^':
            operand2 = operand_stack.pop()
            operand1 = operand_stack.pop()
            result = self.operators[operator](operand1, operand2)
            operand_stack.append(result)
        else:
            operand2 = operand_stack.pop()
            operand1 = operand_stack.pop()
            result = self.operators[operator](operand1, operand2)
            operand_stack.append(result)
        return operand_stack, operator_stack

import unittest

class CalculatorTestCalculate(unittest.TestCase):
    def test_calculate_1(self):
        calculator = Calculator()
        res = calculator.calculate('1+2')
        self.assertEqual(res, 3)

    def test_calculate_2(self):
        calculator = Calculator()
        res = calculator.calculate('1+2*3')
        self.assertEqual(res, 7)

    def test_calculate_3(self):
        calculator = Calculator()
        res = calculator.calculate('1+2*3+4')
        self.assertEqual(res, 11)

    def test_calculate_4(self):
        calculator = Calculator()
        res = calculator.calculate('1+2^3*2+4*5')
        self.assertEqual(res, 37)

    def test_calculate_5(self):
        calculator = Calculator()
        res = calculator.calculate('1+2+3')
        self.assertEqual(res, 6)

    def test_calculate_6(self):
        calculator = Calculator()
        res = calculator.calculate('(1+2)+3')
        self.assertEqual(res, 6)

    def test_calculate_7(self):
        calculator = Calculator()
        res = calculator.calculate('')
        self.assertEqual(res, None)

    def test_calculate_8(self):
        calculator = Calculator()
        res = calculator.calculate('1+2?')
        self.assertEqual(res, 3)


class CalculatorTestPrecedence(unittest.TestCase):
    def test_precedence_1(self):
        calculator = Calculator()
        res1 = calculator.precedence('+')
        res2 = calculator.precedence('-')
        self.assertEqual(res1, res2)

    def test_precedence_2(self):
        calculator = Calculator()
        res1 = calculator.precedence('*')
        res2 = calculator.precedence('/')
        self.assertEqual(res1, res2)

    def test_precedence_3(self):
        calculator = Calculator()
        res1 = calculator.precedence('+')
        res2 = calculator.precedence('/')
        self.assertNotEqual(res1, res2)

    def test_precedence_4(self):
        calculator = Calculator()
        res1 = calculator.precedence('+')
        res2 = calculator.precedence('/')
        self.assertNotEqual(res1, res2)

    def test_precedence_5(self):
        calculator = Calculator()
        res1 = calculator.precedence('*')
        res2 = calculator.precedence('-')
        self.assertNotEqual(res1, res2)

if __name__ == '__main__':
    unittest.main()
