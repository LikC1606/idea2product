import unittest
from unittest.mock import patch, MagicMock
from app.controllers.hints_tutorials import HintsTutorialsController

class TestHintsTutorials(unittest.TestCase):

    def setUp(self):
        self.controller = HintsTutorialsController()

    @patch('app.controllers.hints_tutorials.HintsTutorialsController.get_hints')
    def test_get_hints_for_problem(self, mock_get_hints):
        problem_id = 1
        expected_hints = ["Hint 1", "Hint 2", "Hint 3"]
        mock_get_hints.return_value = expected_hints

        hints = self.controller.get_hints(problem_id)
        mock_get_hints.assert_called_once_with(problem_id)
        self.assertEqual(hints, expected_hints)

    @patch('app.controllers.hints_tutorials.HintsTutorialsController.get_tutorial')
    def test_get_tutorial_for_problem(self, mock_get_tutorial):
        problem_id = 1
        expected_tutorial = "This is a tutorial for problem 1."
        mock_get_tutorial.return_value = expected_tutorial

        tutorial = self.controller.get_tutorial(problem_id)
        mock_get_tutorial.assert_called_once_with(problem_id)
        self.assertEqual(tutorial, expected_tutorial)

    @patch('app.controllers.hints_tutorials.HintsTutorialsController.get_hints')
    def test_get_hints_no_hints_available(self, mock_get_hints):
        problem_id = 2
        mock_get_hints.return_value = []

        hints = self.controller.get_hints(problem_id)
        mock_get_hints.assert_called_once_with(problem_id)
        self.assertEqual(hints, [])

    @patch('app.controllers.hints_tutorials.HintsTutorialsController.get_tutorial')
    def test_get_tutorial_no_tutorial_available(self, mock_get_tutorial):
        problem_id = 2
        mock_get_tutorial.return_value = None

        tutorial = self.controller.get_tutorial(problem_id)
        mock_get_tutorial.assert_called_once_with(problem_id)
        self.assertIsNone(tutorial)

    @patch('app.controllers.hints_tutorials.HintsTutorialsController.get_hints')
    @patch('app.controllers.hints_tutorials.HintsTutorialsController.get_tutorial')
    def test_get_hints_and_tutorial_combined(self, mock_get_tutorial, mock_get_hints):
        problem_id = 3
        expected_hints = ["Hint A", "Hint B"]
        expected_tutorial = "This is a tutorial for problem 3."

        mock_get_hints.return_value = expected_hints
        mock_get_tutorial.return_value = expected_tutorial

        hints = self.controller.get_hints(problem_id)
        tutorial = self.controller.get_tutorial(problem_id)

        mock_get_hints.assert_called_once_with(problem_id)
        mock_get_tutorial.assert_called_once_with(problem_id)

        self.assertEqual(hints, expected_hints)
        self.assertEqual(tutorial, expected_tutorial)

if __name__ == '__main__':
    unittest.main()