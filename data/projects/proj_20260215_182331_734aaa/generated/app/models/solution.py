from app.database import db

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    problem_id = db.Column(db.Integer, nullable=False)
    submission_code = db.Column(db.Text, nullable=False)
    evaluation_result = db.Column(db.Text, nullable=True)
    submission_time = db.Column(db.DateTime, nullable=False, default=db.func.now())

    def __init__(self, user_id, problem_id, submission_code, evaluation_result=None):
        self.user_id = user_id
        self.problem_id = problem_id
        self.submission_code = submission_code
        self.evaluation_result = evaluation_result