import unittest
import json
from app import app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_save_note_success(self):
        response = self.app.post('/notes', json={"content": "Test note"})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("id", data)
        self.assertIn("content", data)
        self.assertIn("created_at", data)
        self.assertEqual(data["content"], "Test note")

    def test_save_note_failure(self):
        response = self.app.post('/notes', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Content is required")

    def test_get_notes(self):
        # Add a sample note
        self.app.post('/notes', json={"content": "Sample note"})
        
        response = self.app.get('/notes')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("id", data[0])
        self.assertIn("content", data[0])
        self.assertIn("created_at", data[0])

if __name__ == '__main__':
    unittest.main()