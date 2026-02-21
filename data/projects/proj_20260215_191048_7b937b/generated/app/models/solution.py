from app.database import db

class Solution:
    def __init__(self, solution_id=None, problem_id=None, user_id=None, code=None, language=None, status=None):
        self.solution_id = solution_id
        self.problem_id = problem_id
        self.user_id = user_id
        self.code = code
        self.language = language
        self.status = status

    def to_dict(self):
        return {
            "solution_id": self.solution_id,
            "problem_id": self.problem_id,
            "user_id": self.user_id,
            "code": self.code,
            "language": self.language,
            "status": self.status,
        }