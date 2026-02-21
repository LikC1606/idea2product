# app/models/problem.py

from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Problem(Base):
    __tablename__ = 'problems'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(50), nullable=False)  # e.g., "Easy", "Medium", "Hard"
    is_active = Column(Boolean, default=True)  # Whether the problem is active or not
    
    def __repr__(self):
        return f"<Problem(id={self.id}, title={self.title}, difficulty={self.difficulty}, is_active={self.is_active})>"