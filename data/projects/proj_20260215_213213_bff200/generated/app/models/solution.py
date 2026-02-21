from app.database import db
from app.models.problem import Problem
from app.models.user import User

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    # Foreign keys
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))

    def __repr__(self):
        return f"<Solution id={self.id} content={self.content[:30]}... problem_id={self.problem_id} user_id={self.user_id}>"