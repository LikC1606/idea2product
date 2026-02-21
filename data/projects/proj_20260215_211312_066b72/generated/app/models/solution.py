from app.database import db
from app.models.user import User
from app.models.problem import Problem
from datetime import datetime

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")  # Possible values: Pending, Accepted, Rejected
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))

    def __repr__(self):
        return f'<Solution {self.id} - User {self.user_id} - Problem {self.problem_id}>'

    def save(self):
        """Save the current solution instance to the database."""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, solution_id):
        """Retrieve a solution by its ID."""
        return cls.query.get(solution_id)

    @classmethod
    def get_all_solutions(cls):
        """Retrieve all solutions."""
        return cls.query.all()

    @classmethod
    def get_by_user_and_problem(cls, user_id, problem_id):
        """Retrieve solutions submitted by a specific user for a specific problem."""
        return cls.query.filter_by(user_id=user_id, problem_id=problem_id).all()