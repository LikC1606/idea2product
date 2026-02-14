import unittest
from src.ai.content_generation import generate_product_description

class TestAIContentGeneration(unittest.TestCase):
    def setUp(self):
        self.test_image_path = "tests/data/sample_image.jpg"
        self.test_description = "A stylish sneaker perfect for daily wear."
        self.expected_output_keys = ["title", "selling_points"]
    
    def test_generate_product_description_valid_input(self):
        result = generate_product_description(self.test_image_path, self.test_description)
        
        # Verify result contains expected keys
        for key in self.expected_output_keys:
            self.assertIn(key, result)
        
        # Verify title and selling points are non-empty strings
        self.assertIsInstance(result["title"], str)
        self.assertGreater(len(result["title"]), 0)
        self.assertIsInstance(result["selling_points"], list)
        self.assertGreater(len(result["selling_points"]), 0)
    
    def test_generate_product_description_empty_description(self):
        result = generate_product_description(self.test_image_path, "")
        
        # Verify behavior when description is empty
        self.assertIn("title", result)
        self.assertIn("selling_points", result)
        self.assertGreater(len(result["title"]), 0)
        self.assertGreater(len(result["selling_points"]), 0)
    
    def test_generate_product_description_invalid_image_path(self):
        with self.assertRaises(FileNotFoundError):
            generate_product_description("invalid/path/to/image.jpg", self.test_description)
    
    def test_generate_product_description_youth_oriented_suggestions(self):
        result = generate_product_description(self.test_image_path, self.test_description)
        
        # Verify generated selling points include youth-oriented suggestions
        youth_keywords = ["trendy", "stylish", "cool", "modern"]
        suggestions = " ".join(result["selling_points"]).lower()
        self.assertTrue(any(keyword in suggestions for keyword in youth_keywords))

if __name__ == "__main__":
    unittest.main()