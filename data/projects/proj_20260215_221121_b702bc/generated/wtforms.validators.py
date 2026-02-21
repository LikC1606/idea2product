from wtforms.validators import ValidationError
from app.models.note import Note
from app.database import db

class UniqueNoteTitle:
    """
    Custom WTForms validator to ensure that the note title is unique for a user.
    """

    def __init__(self, message=None):
        if not message:
            message = "This note title is already in use. Please choose a different title."
        self.message = message

    def __call__(self, form, field):
        user_id = form.user_id.data  # Assumes the form includes user_id
        note_title = field.data

        if db.session.query(Note).filter_by(user_id=user_id, title=note_title).first():
            raise ValidationError(self.message)