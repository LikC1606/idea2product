import os
from src.database.database_setup import DatabaseConnection

class TextInputBackend:
    def __init__(self):
        self.db_connection = DatabaseConnection()

    def process_text_input(self, user_id, product_description):
        # Validate input
        if not product_description or not isinstance(product_description, str):
            raise ValueError("Invalid product description provided.")

        # Store in the database
        self.store_text_input(user_id, product_description)

    def store_text_input(self, user_id, product_description):
        try:
            connection = self.db_connection.get_connection()
            cursor = connection.cursor()

            # SQL query to insert product description into the database
            query = """
            INSERT INTO product_descriptions (user_id, description)
            VALUES (%s, %s)
            """
            cursor.execute(query, (user_id, product_description))
            connection.commit()

        except Exception as e:
            print(f"An error occurred while storing text input: {e}")
        finally:
            cursor.close()
            connection.close()

    def generate_suggestions(self, product_description):
        # Placeholder for AI-powered content generation logic
        # This could involve calling an external AI service or library
        suggestions = self._ai_content_generation(product_description)
        return suggestions

    def _ai_content_generation(self, product_description):
        # Simulate AI suggestions generation
        # In a real implementation, integrate with an AI model/API
        suggestions = [
            f"{product_description} - Perfect for young adults!",
            f"{product_description} - Trendy and stylish choice!",
            f"{product_description} - Ideal for the youth market!",
        ]
        return suggestions

# Example usage
if __name__ == "__main__":
    backend = TextInputBackend()
    user_id = 1
    description = "A stylish backpack suitable for daily use."

    backend.process_text_input(user_id, description)
    suggestions = backend.generate_suggestions(description)
    print(suggestions)