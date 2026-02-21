import unittest
from app.controllers.user_profile import UserProfileController

class TestUserProfile(unittest.TestCase):

    def setUp(self):
        """Set up a mock user profile controller for testing."""
        self.user_profile_controller = UserProfileController()
        self.mock_user_data = {
            'username': 'test_user',
            'email': 'test_user@example.com',
            'bio': 'I love solving problems!',
            'profile_picture': 'default.jpg',
            'problems_solved': 25,
            'rank': 'Advanced'
        }
        self.user_profile_controller.create_profile(self.mock_user_data)

    def test_create_profile(self):
        """Test that a new user profile is created successfully."""
        new_user_data = {
            'username': 'new_user',
            'email': 'new_user@example.com',
            'bio': 'New to programming!',
            'profile_picture': 'default.jpg',
            'problems_solved': 0,
            'rank': 'Beginner'
        }
        result = self.user_profile_controller.create_profile(new_user_data)
        self.assertTrue(result)
        self.assertEqual(
            self.user_profile_controller.get_profile('new_user')['email'],
            'new_user@example.com'
        )

    def test_get_profile(self):
        """Test retrieving an existing user profile."""
        profile = self.user_profile_controller.get_profile('test_user')
        self.assertEqual(profile['email'], self.mock_user_data['email'])
        self.assertEqual(profile['rank'], self.mock_user_data['rank'])

    def test_update_profile(self):
        """Test updating an existing user profile."""
        updated_data = {'bio': 'I am an ACM enthusiast!', 'rank': 'Expert'}
        result = self.user_profile_controller.update_profile('test_user', updated_data)
        self.assertTrue(result)
        profile = self.user_profile_controller.get_profile('test_user')
        self.assertEqual(profile['bio'], 'I am an ACM enthusiast!')
        self.assertEqual(profile['rank'], 'Expert')

    def test_delete_profile(self):
        """Test deleting an existing user profile."""
        result = self.user_profile_controller.delete_profile('test_user')
        self.assertTrue(result)
        profile = self.user_profile_controller.get_profile('test_user')
        self.assertIsNone(profile)

    def test_nonexistent_user(self):
        """Test operations on a nonexistent user."""
        profile = self.user_profile_controller.get_profile('nonexistent_user')
        self.assertIsNone(profile)
        result = self.user_profile_controller.update_profile('nonexistent_user', {'bio': 'Test'})
        self.assertFalse(result)
        result = self.user_profile_controller.delete_profile('nonexistent_user')
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()