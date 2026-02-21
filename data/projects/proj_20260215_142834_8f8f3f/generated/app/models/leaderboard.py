from app.database import db

class Leaderboard(db.Model):
    __tablename__ = 'leaderboards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, score, rank):
        self.user_id = user_id
        self.score = score
        self.rank = rank

def get_leaderboard():
    return Leaderboard.query.order_by(Leaderboard.rank.asc()).all()