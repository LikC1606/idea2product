from app.database import db

class Solution:
    def __init__(self, id=None, problem_id=None, user_id=None, code=None, status=None):
        self.id = id
        self.problem_id = problem_id
        self.user_id = user_id
        self.code = code
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "problem_id": self.problem_id,
            "user_id": self.user_id,
            "code": self.code,
            "status": self.status
        }