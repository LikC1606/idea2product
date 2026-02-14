import unittest
from src.backend.text_input_backend import process_text_input

class TestTextInputFeature(unittest.TestCase):
    def setUp(self):
        # Prepare any necessary setup for the tests
        self.valid_input = "This is a test description for a product."
        self.empty_input = ""
        self.special_characters_input = "@#$%^&*()_+{}|:?><"
        self.long_input = "This is a very long test description. " * 50
        self.expected_output = {
            "title": "Test Product Description",
            "selling_points": [
                "Feature 1: High quality",
                "Feature 2: Affordable price",
                "Feature 3: Youth-oriented design"
            ]
        }

    def test_valid_input(self):
        result = process_text_input(self.valid_input)
        self.assertIsInstance(result, dict)
        self.assertIn("title", result)
        self.assertIn("selling_points", result)
        self.assertGreater(len(result["selling_points"]), 0)

    def test_empty_input(self):
        result = process_text_input(self.empty_input)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["title"], "")
        self.assertEqual(result["selling_points"], [])

    def test_special_characters_input(self):
        result = process_text_input(self.special_characters_input)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["title"], "Special Character Product")
        self.assertGreater(len(result["selling_points"]), 0)

    def test_long_input(self):
        result = process_text_input(self.long_input)
        self.assertIsInstance(result, dict)
        self.assertIn("title", result)
        self.assertIn("selling_points", result)
        self.assertGreater(len(result["selling_points"]), 0)

    def test_output_format(self):
        result = process_text_input(self.valid_input)
        self.assertEqual(set(result.keys()), {"title", "selling_points"})
        self.assertIsInstance(result["title"], str)
        self.assertIsInstance(result["selling_points"], list)

if __name__ == "__main__":
    unittest.main()