# src/ai/content_generation.py

import os
from src.backend.text_input_backend import process_text_input
from src.backend.image_upload_backend import process_image_upload
from ai_model import generate_product_descriptions  # Assuming an AI model integration

class ContentGenerator:
    def __init__(self):
        self.image_data = None
        self.text_data = None

    def upload_image(self, image_file_path):
        if not os.path.exists(image_file_path):
            raise FileNotFoundError("Image file not found.")
        self.image_data = process_image_upload(image_file_path)

    def input_text(self, text):
        if not text:
            raise ValueError("Text input cannot be empty.")
        self.text_data = process_text_input(text)

    def generate_content(self):
        if not self.image_data or not self.text_data:
            raise ValueError("Both image and text input are required to generate content.")
        return generate_product_descriptions(self.image_data, self.text_data)

# Example usage
if __name__ == "__main__":
    generator = ContentGenerator()
    try:
        # Simulate user input
        generator.upload_image("path/to/image.jpg")
        generator.input_text("Trendy backpack for teenagers, spacious and stylish.")
        
        # Generate and display content
        generated_content = generator.generate_content()
        print("Generated Content:")
        print(generated_content)
    except Exception as e:
        print(f"Error: {e}")