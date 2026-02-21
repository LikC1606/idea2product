from app.database import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Leaderboard(db.Model):
    __tablename__ = 'leaderboards'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    score = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)

    user = relationship('User', back_populates='leaderboard_entries')

    def __init__(self, user_id, score, rank):
        self.user_id = user_id
        self.score = score
        self.rank = rank