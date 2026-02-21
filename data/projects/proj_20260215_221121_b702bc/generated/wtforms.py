from wtforms import Form, StringField, TextAreaField, validators

class NoteForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=1, max=255)
    ])
    content = TextAreaField('Content', [
        validators.DataRequired(),
        validators.Length(min=1)
    ])