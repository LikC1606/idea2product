# Module: app.models.note
# Imports: from app.database import db, from datetime import datetime
# Export: Note (class)

from app.database import db
from datetime import datetime

class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, title, content):
        self.title = title
        self.content = content

    def __repr__(self):
        return f'<Note {self.id}: {self.title}>'