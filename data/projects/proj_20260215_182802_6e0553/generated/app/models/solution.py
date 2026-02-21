from app.database import db

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    problem_id = db.Column(db.Integer, nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def __init__(self, user_id, problem_id, code, language):
        self.user_id = user_id
        self.problem_id = problem_id
        self.code = code
        self.language = language