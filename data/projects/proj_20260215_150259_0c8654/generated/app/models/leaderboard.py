from app.database import db

class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, score, rank):
        self.user_id = user_id
        self.score = score
        self.rank = rank

    def __repr__(self):
        return f"<Leaderboard(id={self.id}, user_id={self.user_id}, score={self.score}, rank={self.rank})>"

def get_leaderboard(limit=10):
    """
    Fetch the top players from the leaderboard.

    :param limit: Number of top players to fetch (default is 10)
    :return: List of Leaderboard instances
    """
    return Leaderboard.query.order_by(Leaderboard.rank.asc()).limit(limit).all()