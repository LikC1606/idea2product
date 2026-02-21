from app.database import db
from datetime import datetime

class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    input_description = db.Column(db.Text, nullable=False)
    output_description = db.Column(db.Text, nullable=False)
    sample_input = db.Column(db.Text, nullable=False)
    sample_output = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Enum('Easy', 'Medium', 'Hard', name='difficulty_levels'), nullable=False, default='Medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Problem {self.title} ({self.difficulty})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'input_description': self.input_description,
            'output_description': self.output_description,
            'sample_input': self.sample_input,
            'sample_output': self.sample_output,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }