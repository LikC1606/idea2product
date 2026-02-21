from sqlalchemy import Column, Integer, String, Text
from app.database import db

class Problem(db.Model):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Problem(id={self.id}, title={self.title}, difficulty={self.difficulty}, category={self.category})>"