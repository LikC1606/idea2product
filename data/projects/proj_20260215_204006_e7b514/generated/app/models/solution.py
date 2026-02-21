from app.database import db
from app.models.problem import Problem
from app.models.user import User

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    result = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))

    def __repr__(self):
        return f"<Solution id={self.id} user_id={self.user_id} problem_id={self.problem_id} result={self.result}>"