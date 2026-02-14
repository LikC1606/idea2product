import unittest
from unittest.mock import patch
from app.services.content_generator import ContentGenerator

class TestContentGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = ContentGenerator()

    @patch('app.services.content_generator.some_image_processing_function')
    @patch('app.services.content_generator.some_text_generation_function')
    def test_generate_content(self, mock_text_gen, mock_image_proc):
        # Mock the outputs of the image processing and text generation functions
        mock_image_proc.return_value = "processed_image_data"
        mock_text_gen.return_value = {
            "title": "Amazing Product Title",
            "selling_points": [
                "High-quality and durable material",
                "Innovative design tailored to your needs",
                "Affordable price for exceptional value"
            ]
        }

        # Input data
        mock_image = b"mock_image_data"
        mock_description = "A compact and stylish backpack for travel and daily use."

        # Expected outputs
        expected_output = {
            "title": "Amazing Product Title",
            "selling_points": [
                "High-quality and durable material",
                "Innovative design tailored to your needs",
                "Affordable price for exceptional value"
            ]
        }

        # Call the generate_content method
        result = self.generator.generate_content(mock_image, mock_description)

        # Assertions
        mock_image_proc.assert_called_once_with(mock_image)
        mock_text_gen.assert_called_once_with("processed_image_data", mock_description)
        self.assertEqual(result, expected_output)

    def test_generate_content_invalid_input(self):
        # Test with invalid input data
        invalid_image = None
        invalid_description = ""

        with self.assertRaises(ValueError):
            self.generator.generate_content(invalid_image, invalid_description)

if __name__ == '__main__':
    unittest.main()