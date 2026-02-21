from datetime import datetime
from app.database import db

class LeaderboardEntry(db.Model):
    __tablename__ = 'leaderboard'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=False)
    total_score = db.Column(db.Float, nullable=False, default=0.0)
    problems_solved = db.Column(db.Integer, nullable=False, default=0)
    last_submission = db.Column(db.DateTime, nullable=True)

    def __init__(self, user_id, username, total_score=0.0, problems_solved=0, last_submission=None):
        self.user_id = user_id
        self.username = username
        self.total_score = total_score
        self.problems_solved = problems_solved
        self.last_submission = last_submission or datetime.utcnow()

    def update_score(self, score, problem_solved=True):
        self.total_score += score
        if problem_solved:
            self.problems_solved += 1
        self.last_submission = datetime.utcnow()

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "total_score": self.total_score,
            "problems_solved": self.problems_solved,
            "last_submission": self.last_submission.isoformat() if self.last_submission else None
        }