import unittest
from app.controllers.leaderboard import get_leaderboard, update_leaderboard

class TestLeaderboard(unittest.TestCase):

    def setUp(self):
        # Mock data for testing
        self.mock_users = [
            {"username": "user1", "score": 1500},
            {"username": "user2", "score": 1800},
            {"username": "user3", "score": 1700},
        ]
        self.updated_user = {"username": "user4", "score": 1900}

    def test_get_leaderboard(self):
        # Simulate fetching leaderboard data
        leaderboard = get_leaderboard(self.mock_users)
        self.assertIsInstance(leaderboard, list)
        self.assertEqual(len(leaderboard), 3)
        self.assertEqual(leaderboard[0]["username"], "user2")
        self.assertEqual(leaderboard[0]["score"], 1800)

    def test_update_leaderboard(self):
        # Simulate updating the leaderboard
        updated_leaderboard = update_leaderboard(self.mock_users, self.updated_user)
        self.assertIsInstance(updated_leaderboard, list)
        self.assertEqual(len(updated_leaderboard), 4)
        self.assertEqual(updated_leaderboard[0]["username"], "user4")
        self.assertEqual(updated_leaderboard[0]["score"], 1900)

    def test_leaderboard_sorting(self):
        # Verify leaderboard is sorted by score in descending order
        updated_leaderboard = update_leaderboard(self.mock_users, self.updated_user)
        scores = [user["score"] for user in updated_leaderboard]
        self.assertEqual(scores, sorted(scores, reverse=True))

if __name__ == "__main__":
    unittest.main()