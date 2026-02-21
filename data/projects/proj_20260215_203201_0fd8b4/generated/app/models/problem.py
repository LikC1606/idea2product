from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base

class Problem(Base):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    difficulty = Column(String(50), nullable=False)  # e.g., 'easy', 'medium', 'hard'
    is_active = Column(Boolean, default=True)  # Indicates if the problem is available for users

    def __repr__(self):
        return f"<Problem(id={self.id}, title='{self.title}', difficulty='{self.difficulty}', is_active={self.is_active})>"