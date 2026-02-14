import os
from PIL import Image
import openai

class ContentGenerator:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        openai.api_key = self.openai_api_key

    def validate_image(self, image_path):
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except (IOError, OSError):
            return False

    def generate_content(self, description):
        """
        Generates product content including a title and three selling points
        based on the provided description.
        """
        prompt = (
            f"Generate a creative and compelling e-commerce product title and three selling points "
            f"based on the following product description:\n\n{description}\n\n"
            f"Output format:\nTitle: <product_title>\n1. <selling_point_1>\n2. <selling_point_2>\n3. <selling_point_3>"
        )

        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7,
            )
            result = response["choices"][0]["text"].strip()
            return result
        except Exception as e:
            return f"Error generating content: {str(e)}"

    def process_request(self, image_path, description):
        if not os.path.exists(image_path):
            return "Error: Image file does not exist."

        if not self.validate_image(image_path):
            return "Error: Invalid image file."

        if not description or len(description.strip()) == 0:
            return "Error: Product description is required."

        return self.generate_content(description)