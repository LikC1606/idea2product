from app.database import db
from app.models.user import User
from app.models.problem import Problem
from datetime import datetime

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref='solutions', lazy=True)
    problem = db.relationship('Problem', backref='solutions', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'problem_id': self.problem_id,
            'code': self.code,
            'language': self.language,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'is_correct': self.is_correct
        }