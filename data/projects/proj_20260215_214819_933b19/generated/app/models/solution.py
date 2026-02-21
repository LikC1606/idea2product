from app.database import db
from app.models.problem import Problem
from app.models.user import User

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())

    # Foreign keys
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))

    def __init__(self, content, problem_id, user_id):
        self.content = content
        self.problem_id = problem_id
        self.user_id = user_id

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'problem_id': self.problem_id,
            'user_id': self.user_id
        }