from app.database import db
from app.models.problem import Problem
from app.models.user import User

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    result = db.Column(db.String(20), nullable=False)  # e.g., "Accepted", "Wrong Answer"
    submission_time = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Foreign key to associate with a User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))

    # Foreign key to associate with a Problem
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))

    def __repr__(self):
        return f"<Solution id={self.id} user_id={self.user_id} problem_id={self.problem_id} result={self.result}>"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'language': self.language,
            'result': self.result,
            'submission_time': self.submission_time.isoformat(),
            'user_id': self.user_id,
            'problem_id': self.problem_id,
        }