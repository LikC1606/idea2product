import unittest
from io import BytesIO
from app import app

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Product Content Generator', response.data)

    def test_generate_content_with_valid_input(self):
        data = {
            'description': 'A stylish black leather jacket perfect for winter.',
            'image': (BytesIO(b'test_image_data'), 'test_image.jpg')
        }
        response = self.app.post('/generate-content', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Generated Product Title:', response.data)
        self.assertIn(b'Selling Point 1:', response.data)
        self.assertIn(b'Selling Point 2:', response.data)
        self.assertIn(b'Selling Point 3:', response.data)

    def test_generate_content_with_missing_description(self):
        data = {
            'image': (BytesIO(b'test_image_data'), 'test_image.jpg')
        }
        response = self.app.post('/generate-content', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Description is required', response.data)

    def test_generate_content_with_missing_image(self):
        data = {
            'description': 'A stylish black leather jacket perfect for winter.'
        }
        response = self.app.post('/generate-content', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Image is required', response.data)

    def test_generate_content_with_invalid_image_format(self):
        data = {
            'description': 'A stylish black leather jacket perfect for winter.',
            'image': (BytesIO(b'test_invalid_image_data'), 'test_image.txt')
        }
        response = self.app.post('/generate-content', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid image format', response.data)

if __name__ == '__main__':
    unittest.main()