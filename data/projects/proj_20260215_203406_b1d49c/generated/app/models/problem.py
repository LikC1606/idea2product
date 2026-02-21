from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Problem(Base):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(50), nullable=False)
    tags = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Problem(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"