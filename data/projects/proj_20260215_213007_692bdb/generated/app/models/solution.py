from app.database import db
from app.models.problem import Problem
from app.models.user import User

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    problem = db.relationship('Problem', back_populates='solutions')
    user = db.relationship('User', back_populates='solutions')

    def __repr__(self):
        return f"<Solution id={self.id}, problem_id={self.problem_id}, user_id={self.user_id}>"

# Add relationship attributes to related models
Problem.solutions = db.relationship('Solution', back_populates='problem', cascade='all, delete-orphan')
User.solutions = db.relationship('Solution', back_populates='user', cascade='all, delete-orphan')