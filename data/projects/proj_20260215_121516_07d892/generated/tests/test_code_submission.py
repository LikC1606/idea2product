import unittest
from app.controllers.code_submission import CodeSubmissionController

class TestCodeSubmission(unittest.TestCase):

    def setUp(self):
        # Initialize the controller for code submission
        self.controller = CodeSubmissionController()

    def test_valid_submission(self):
        # Test a valid code submission
        code = "print('Hello, World!')"
        problem_id = 1
        user_id = 101
        result = self.controller.submit_code(user_id, problem_id, code)
        self.assertTrue(result['success'])
        self.assertIn('execution_time', result)
        self.assertIn('memory_used', result)

    def test_invalid_submission(self):
        # Test an invalid submission with errors in code
        code = "print('Hello, World!'"
        problem_id = 1
        user_id = 101
        result = self.controller.submit_code(user_id, problem_id, code)
        self.assertFalse(result['success'])
        self.assertIn('error_message', result)

    def test_evaluation_correct_solution(self):
        # Test evaluation for a correct solution
        code = "print(2 + 2)"
        problem_id = 2
        user_id = 102
        result = self.controller.submit_code(user_id, problem_id, code)
        self.assertTrue(result['success'])
        self.assertTrue(result['is_correct'])

    def test_evaluation_incorrect_solution(self):
        # Test evaluation for an incorrect solution
        code = "print(2 * 2)"
        problem_id = 2
        user_id = 103
        result = self.controller.submit_code(user_id, problem_id, code)
        self.assertTrue(result['success'])
        self.assertFalse(result['is_correct'])

    def test_submission_limits(self):
        # Test user submission limits
        user_id = 104
        problem_id = 3
        code = "print('Test Submission')"
        for _ in range(5):  # Assuming the limit is 5 submissions
            self.controller.submit_code(user_id, problem_id, code)
        
        result = self.controller.submit_code(user_id, problem_id, code)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_message'], "Submission limit reached")

    def test_edge_case_submission(self):
        # Test edge case with empty code submission
        code = ""
        problem_id = 4
        user_id = 105
        result = self.controller.submit_code(user_id, problem_id, code)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_message'], "Code cannot be empty")

if __name__ == '__main__':
    unittest.main()