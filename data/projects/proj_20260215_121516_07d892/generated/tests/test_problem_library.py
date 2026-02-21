import unittest
from app.controllers.problem_library import ProblemLibrary

class TestProblemLibrary(unittest.TestCase):
    def setUp(self):
        # Initialize ProblemLibrary instance for testing
        self.problem_library = ProblemLibrary()

    def test_get_all_problems(self):
        # Test retrieving all problems
        problems = self.problem_library.get_all_problems()
        self.assertIsInstance(problems, list)
        self.assertGreater(len(problems), 0, "Problem library should not be empty")

    def test_get_problem_by_id(self):
        # Test retrieving a problem by ID
        problem_id = 1  # Assuming ID 1 exists in the library
        problem = self.problem_library.get_problem_by_id(problem_id)
        self.assertIsNotNone(problem)
        self.assertEqual(problem['id'], problem_id)
        self.assertIn('name', problem)
        self.assertIn('description', problem)

    def test_add_problem(self):
        # Test adding a new problem to the library
        new_problem = {
            'name': 'Sample Problem',
            'description': 'Solve this sample problem.',
            'difficulty': 'Easy',
            'tags': ['math', 'dp']
        }
        response = self.problem_library.add_problem(new_problem)
        self.assertTrue(response['success'])
        self.assertIn('id', response)
        added_problem = self.problem_library.get_problem_by_id(response['id'])
        self.assertEqual(added_problem['name'], new_problem['name'])
        self.assertEqual(added_problem['description'], new_problem['description'])
        self.assertEqual(added_problem['difficulty'], new_problem['difficulty'])
        self.assertListEqual(added_problem['tags'], new_problem['tags'])

    def test_update_problem(self):
        # Test updating an existing problem
        updated_data = {
            'name': 'Updated Problem Name',
            'description': 'Updated description.',
            'difficulty': 'Medium',
            'tags': ['math', 'geometry']
        }
        problem_id = 1  # Assuming ID 1 exists in the library
        response = self.problem_library.update_problem(problem_id, updated_data)
        self.assertTrue(response['success'])
        updated_problem = self.problem_library.get_problem_by_id(problem_id)
        self.assertEqual(updated_problem['name'], updated_data['name'])
        self.assertEqual(updated_problem['description'], updated_data['description'])
        self.assertEqual(updated_problem['difficulty'], updated_data['difficulty'])
        self.assertListEqual(updated_problem['tags'], updated_data['tags'])

    def test_delete_problem(self):
        # Test deleting a problem from the library
        problem_id = 1  # Assuming ID 1 exists in the library
        response = self.problem_library.delete_problem(problem_id)
        self.assertTrue(response['success'])
        deleted_problem = self.problem_library.get_problem_by_id(problem_id)
        self.assertIsNone(deleted_problem)

    def test_search_problems_by_tag(self):
        # Test searching problems by tag
        tag = 'math'
        problems = self.problem_library.search_problems_by_tag(tag)
        self.assertIsInstance(problems, list)
        for problem in problems:
            self.assertIn(tag, problem['tags'])

    def test_filter_problems_by_difficulty(self):
        # Test filtering problems by difficulty level
        difficulty = 'Easy'
        problems = self.problem_library.filter_problems_by_difficulty(difficulty)
        self.assertIsInstance(problems, list)
        for problem in problems:
            self.assertEqual(problem['difficulty'], difficulty)

if __name__ == '__main__':
    unittest.main()