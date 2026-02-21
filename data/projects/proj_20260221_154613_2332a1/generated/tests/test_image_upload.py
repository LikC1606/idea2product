import unittest
import os
from werkzeug.datastructures import FileStorage
from app.routes import upload_image
from app.static.uploads import UPLOAD_FOLDER

class TestImageUpload(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_image_path = 'tests/test_images/test_image.jpg'
        self.uploaded_image_path = os.path.join(UPLOAD_FOLDER, 'test_image.jpg')

        # Create a dummy image for testing
        with open(self.test_image_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00')

    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.uploaded_image_path):
            os.remove(self.uploaded_image_path)
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_upload_image_success(self):
        """Test successful image upload."""
        with open(self.test_image_path, 'rb') as f:
            file = FileStorage(f, filename='test_image.jpg', content_type='image/jpeg')
            response = upload_image(file)
            self.assertTrue(os.path.exists(self.uploaded_image_path))
            self.assertEqual(response, 'Image uploaded successfully.')

    def test_upload_image_invalid_format(self):
        """Test image upload with invalid format."""
        invalid_image_path = 'tests/test_images/test_invalid_image.txt'
        with open(invalid_image_path, 'w') as f:
            f.write("This is not an image file.")
        
        with open(invalid_image_path, 'rb') as f:
            file = FileStorage(f, filename='test_invalid_image.txt', content_type='text/plain')
            response = upload_image(file)
            self.assertFalse(os.path.exists(os.path.join(UPLOAD_FOLDER, 'test_invalid_image.txt')))
            self.assertEqual(response, 'Invalid file format.')

        if os.path.exists(invalid_image_path):
            os.remove(invalid_image_path)