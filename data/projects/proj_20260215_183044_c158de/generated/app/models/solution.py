from app.database import db

class Solution():
    def __init__(self, id=None, problem_id=None, user_id=None, code=None, is_correct=None, submission_time=None):
        self.id = id
        self.problem_id = problem_id
        self.user_id = user_id
        self.code = code
        self.is_correct = is_correct
        self.submission_time = submission_time

    def to_dict(self):
        return {
            "id": self.id,
            "problem_id": self.problem_id,
            "user_id": self.user_id,
            "code": self.code,
            "is_correct": self.is_correct,
            "submission_time": self.submission_time
        }