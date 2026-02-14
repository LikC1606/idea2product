from calculator_app.ui import CalculatorUI
from calculator_app.operations import add, subtract, multiply, divide


class CalculatorBackend:
    def __init__(self):
        self.ui = CalculatorUI()
        self.ui.set_calculate_callback(self.calculate)

    def calculate(self, operation, num1, num2):
        try:
            num1 = float(num1)
            num2 = float(num2)
        except ValueError:
            self.ui.display_result("Error: Invalid input")
            return

        if operation == "add":
            result = add(num1, num2)
        elif operation == "subtract":
            result = subtract(num1, num2)
        elif operation == "multiply":
            result = multiply(num1, num2)
        elif operation == "divide":
            if num2 == 0:
                self.ui.display_result("Error: Division by zero")
                return
            result = divide(num1, num2)
        else:
            self.ui.display_result("Error: Unknown operation")
            return

        self.ui.display_result(result)

    def run(self):
        self.ui.run()


if __name__ == "__main__":
    backend = CalculatorBackend()
    backend.run()