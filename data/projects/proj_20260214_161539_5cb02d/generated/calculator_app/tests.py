import unittest
from calculator_app.backend import Calculator

class TestCalculatorOperations(unittest.TestCase):

    def setUp(self):
        self.calculator = Calculator()

    def test_addition(self):
        result = self.calculator.add(5, 3)
        self.assertEqual(result, 8, "Addition test failed!")

    def test_subtraction(self):
        result = self.calculator.subtract(10, 4)
        self.assertEqual(result, 6, "Subtraction test failed!")

    def test_multiplication(self):
        result = self.calculator.multiply(7, 3)
        self.assertEqual(result, 21, "Multiplication test failed!")

    def test_division(self):
        result = self.calculator.divide(12, 4)
        self.assertEqual(result, 3, "Division test failed!")

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            self.calculator.divide(5, 0)

class TestCalculatorUIIntegration(unittest.TestCase):
    # Simulated UI integration testing
    def test_ui_addition(self):
        # Simulate user entering 5 + 3 and pressing "="
        input_expression = "5 + 3"
        expected_output = 8
        actual_output = self.simulate_ui(input_expression)
        self.assertEqual(actual_output, expected_output, "UI Addition test failed!")

    def test_ui_subtraction(self):
        # Simulate user entering 10 - 4 and pressing "="
        input_expression = "10 - 4"
        expected_output = 6
        actual_output = self.simulate_ui(input_expression)
        self.assertEqual(actual_output, expected_output, "UI Subtraction test failed!")

    def test_ui_multiplication(self):
        # Simulate user entering 7 * 3 and pressing "="
        input_expression = "7 * 3"
        expected_output = 21
        actual_output = self.simulate_ui(input_expression)
        self.assertEqual(actual_output, expected_output, "UI Multiplication test failed!")

    def test_ui_division(self):
        # Simulate user entering 12 / 4 and pressing "="
        input_expression = "12 / 4"
        expected_output = 3
        actual_output = self.simulate_ui(input_expression)
        self.assertEqual(actual_output, expected_output, "UI Division test failed!")

    def simulate_ui(self, expression):
        # Mock method to simulate UI behavior; in practice, connect to the actual UI layer
        try:
            operands, operator = self.parse_expression(expression)
            if operator == "+":
                return self.calculator.add(*operands)
            elif operator == "-":
                return self.calculator.subtract(*operands)
            elif operator == "*":
                return self.calculator.multiply(*operands)
            elif operator == "/":
                return self.calculator.divide(*operands)
        except ZeroDivisionError:
            return "Error: Division by zero"

    def parse_expression(self, expression):
        # Parses the input expression like "5 + 3" into operands and operator
        tokens = expression.split()
        operand1 = int(tokens[0])
        operator = tokens[1]
        operand2 = int(tokens[2])
        return (operand1, operand2), operator

if __name__ == "__main__":
    unittest.main()