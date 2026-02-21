import unittest
import json
from app import create_app, db
from app.models import Note

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_post_notes(self):
        response = self.client.post('/notes', json={'content': 'Test Note'})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', data)
        self.assertIn('content', data)
        self.assertIn('created_at', data)

    def test_get_notes(self):
        note = Note(content="Test Note")
        db.session.add(note)
        db.session.commit()
        response = self.client.get('/notes')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)

    def test_search_notes(self):
        note = Note(content="Searchable Note")
        db.session.add(note)
        db.session.commit()
        response = self.client.get('/notes/search', query_string={'query': 'Searchable'})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)

if __name__ == '__main__':
    unittest.main()