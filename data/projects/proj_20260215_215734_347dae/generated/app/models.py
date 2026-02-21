from app.database import db

class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, title, content):
        self.title = title
        self.content = content

    def save(self):
        """
        Save the current note instance to the database.
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Delete the current note instance from the database.
        """
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all_notes():
        """
        Retrieve all notes from the database.
        """
        return Note.query.all()

    @staticmethod
    def get_note_by_id(note_id):
        """
        Retrieve a single note by its ID.
        """
        return Note.query.get(note_id)

    @staticmethod
    def search_notes(query):
        """
        Search notes by title or content that contains the query string.
        """
        return Note.query.filter(
            db.or_(
                Note.title.ilike(f'%{query}%'),
                Note.content.ilike(f'%{query}%')
            )
        ).all()