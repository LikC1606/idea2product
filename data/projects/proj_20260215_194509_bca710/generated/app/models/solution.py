# app/models/solution.py

from app.database import db

class Solution:
    def __init__(self, solution_id=None, problem_id=None, user_id=None, code=None, status=None):
        self.solution_id = solution_id
        self.problem_id = problem_id
        self.user_id = user_id
        self.code = code
        self.status = status

    def to_dict(self):
        """Convert the Solution object to a dictionary."""
        return {
            "solution_id": self.solution_id,
            "problem_id": self.problem_id,
            "user_id": self.user_id,
            "code": self.code,
            "status": self.status
        }

    @staticmethod
    def from_dict(data):
        """Create a Solution object from a dictionary."""
        return Solution(
            solution_id=data.get("solution_id"),
            problem_id=data.get("problem_id"),
            user_id=data.get("user_id"),
            code=data.get("code"),
            status=data.get("status")
        )