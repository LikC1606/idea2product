from app.database import db

class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return f'<Note {self.id}: {self.content[:20]}...>'