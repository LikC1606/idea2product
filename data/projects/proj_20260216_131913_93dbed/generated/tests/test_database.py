import unittest
from app import db, create_app
from app.models import Note

class TestDatabaseModels(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_note_creation(self):
        note = Note(content="Sample Note")
        db.session.add(note)
        db.session.commit()
        self.assertEqual(Note.query.count(), 1)
        self.assertEqual(Note.query.first().content, "Sample Note")

    def test_note_query(self):
        note1 = Note(content="First Note")
        note2 = Note(content="Second Note")
        db.session.add(note1)
        db.session.add(note2)
        db.session.commit()
        notes = Note.query.all()
        self.assertEqual(len(notes), 2)

    def test_note_search(self):
        note = Note(content="Search Note")
        db.session.add(note)
        db.session.commit()
        search_results = Note.query.filter(Note.content.contains("Search")).all()
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0].content, "Search Note")

if __name__ == '__main__':
    unittest.main()