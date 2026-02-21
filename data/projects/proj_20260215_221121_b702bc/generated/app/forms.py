from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class CreateNoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Create Note')

class SearchNotesForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Search')