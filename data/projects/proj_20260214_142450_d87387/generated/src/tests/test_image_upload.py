import unittest
import os
from werkzeug.datastructures import FileStorage
from src.backend.image_upload_backend import process_image_upload

class TestImageUploadFeature(unittest.TestCase):
    def setUp(self):
        """
        Set up necessary variables and mock data for testing.
        """
        self.test_image_path = "tests/test_images/sample_image.jpg"
        self.test_image_upload_name = "sample_image.jpg"
        self.invalid_file_path = "tests/test_images/invalid_file.txt"
        self.valid_file_type = "image/jpeg"
        self.invalid_file_type = "text/plain"
        self.uploaded_images_directory = "uploads/"
        
        # Ensure the uploads directory exists for testing
        if not os.path.exists(self.uploaded_images_directory):
            os.makedirs(self.uploaded_images_directory)

    def tearDown(self):
        """
        Clean up after tests by removing any uploaded files.
        """
        if os.path.exists(self.uploaded_images_directory):
            for file in os.listdir(self.uploaded_images_directory):
                file_path = os.path.join(self.uploaded_images_directory, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)

    def create_mock_file(self, path, file_type):
        """
        Create a mock FileStorage object for testing.
        """
        with open(path, "rb") as file:
            return FileStorage(
                stream=file,
                filename=os.path.basename(path),
                content_type=file_type
            )

    def test_successful_image_upload(self):
        """
        Test if a valid image file is successfully uploaded and processed.
        """
        mock_file = self.create_mock_file(self.test_image_path, self.valid_file_type)
        response = process_image_upload(mock_file, self.uploaded_images_directory)

        # Check if the file was saved correctly
        saved_file_path = os.path.join(self.uploaded_images_directory, self.test_image_upload_name)
        self.assertTrue(os.path.exists(saved_file_path))
        self.assertEqual(response["status"], "success")
        self.assertIn("message", response)
        self.assertEqual(response["message"], "File uploaded successfully.")

    def test_invalid_file_type_upload(self):
        """
        Test if an invalid file type is rejected during upload.
        """
        mock_file = self.create_mock_file(self.invalid_file_path, self.invalid_file_type)
        response = process_image_upload(mock_file, self.uploaded_images_directory)

        # Assert that the upload was rejected
        self.assertEqual(response["status"], "error")
        self.assertIn("message", response)
        self.assertEqual(response["message"], "Invalid file type. Only images are allowed.")

    def test_empty_file_upload(self):
        """
        Test if an empty file upload is handled properly.
        """
        empty_mock_file = FileStorage(
            stream=None,
            filename="",
            content_type=""
        )
        response = process_image_upload(empty_mock_file, self.uploaded_images_directory)

        # Assert that the upload was rejected
        self.assertEqual(response["status"], "error")
        self.assertIn("message", response)
        self.assertEqual(response["message"], "No file provided.")

    def test_large_file_upload(self):
        """
        Test if a file exceeding the size limit is rejected.
        """
        # Assuming the backend restricts file size to 5MB
        large_file_path = "tests/test_images/large_image.jpg"
        mock_file = self.create_mock_file(large_file_path, self.valid_file_type)

        # Simulate a file size check (add actual size logic in process_image_upload if needed)
        response = process_image_upload(mock_file, self.uploaded_images_directory)

        # Assert that the upload was rejected
        self.assertEqual(response["status"], "error")
        self.assertIn("message", response)
        self.assertEqual(response["message"], "File size exceeds the allowed limit.")

if __name__ == "__main__":
    unittest.main()