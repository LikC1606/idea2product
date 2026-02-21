from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class NoteForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(message="Title is required."),
        Length(max=255, message="Title must be 255 characters or fewer.")
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(message="Content is required.")
    ])
    submit = SubmitField('Save Note')