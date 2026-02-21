import unittest
from app.routes import create_post, upload_image
from app.models import BlogPost, Image
from app.forms import BlogPostForm, ImageUploadForm
from unittest.mock import patch, MagicMock

class TestBlogPostCreation(unittest.TestCase):

    @patch('app.routes.BlogPostForm')
    @patch('app.routes.BlogPost')
    def test_create_post_success(self, MockBlogPost, MockBlogPostForm):
        # Mock the form validation to return True
        form = MockBlogPostForm.return_value
        form.validate_on_submit.return_value = True
        form.title.data = "Test Blog Post"
        form.content.data = "This is a test blog post."

        # Call the create_post function
        response = create_post()

        # Assert that a new BlogPost object was created
        MockBlogPost.assert_called_once_with(title="Test Blog Post", content="This is a test blog post.")

        # Assert the response is a success (mocked response)
        self.assertEqual(response, "Post Created")

    @patch('app.routes.BlogPostForm')
    def test_create_post_validation_failure(self, MockBlogPostForm):
        # Mock the form validation to return False
        form = MockBlogPostForm.return_value
        form.validate_on_submit.return_value = False

        # Call the create_post function
        response = create_post()

        # Assert that no BlogPost object was created
        self.assertEqual(response, "Validation Failed")

    @patch('app.routes.ImageUploadForm')
    @patch('app.routes.Image')
    def test_upload_image_success(self, MockImage, MockImageUploadForm):
        # Mock the form validation to return True
        form = MockImageUploadForm.return_value
        form.validate_on_submit.return_value = True
        form.image.data = MagicMock(filename="test_image.jpg")

        # Call the upload_image function
        response = upload_image()

        # Assert that a new Image object was created
        MockImage.assert_called_once_with(filename="test_image.jpg")

        # Assert the response is a success (mocked response)
        self.assertEqual(response, "Image Uploaded")

    @patch('app.routes.ImageUploadForm')
    def test_upload_image_validation_failure(self, MockImageUploadForm):
        # Mock the form validation to return False
        form = MockImageUploadForm.return_value
        form.validate_on_submit.return_value = False

        # Call the upload_image function
        response = upload_image()

        # Assert that no Image object was created
        self.assertEqual(response, "Validation Failed")

if __name__ == '__main__':
    unittest.main()