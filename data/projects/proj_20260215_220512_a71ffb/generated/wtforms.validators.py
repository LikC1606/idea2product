from wtforms.validators import ValidationError

class NoteTitleValidator:
    def __init__(self, min_length=3, max_length=255):
        self.min_length = min_length
        self.max_length = max_length

    def __call__(self, form, field):
        title = field.data.strip()
        if not title:
            raise ValidationError("Title cannot be empty.")
        if len(title) < self.min_length:
            raise ValidationError(f"Title must be at least {self.min_length} characters long.")
        if len(title) > self.max_length:
            raise ValidationError(f"Title must be no more than {self.max_length} characters long.")

class NoteContentValidator:
    def __init__(self, min_length=10):
        self.min_length = min_length

    def __call__(self, form, field):
        content = field.data.strip()
        if not content:
            raise ValidationError("Content cannot be empty.")
        if len(content) < self.min_length:
            raise ValidationError(f"Content must be at least {self.min_length} characters long.")