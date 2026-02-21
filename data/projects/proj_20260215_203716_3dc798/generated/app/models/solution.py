from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Solution(Base):
    __tablename__ = 'solutions'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False)
    language = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=False)

    user = relationship("User", back_populates="solutions")
    problem = relationship("Problem", back_populates="solutions")