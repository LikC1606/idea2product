from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.problem import Problem
from app.models.user import User

class Solution(Base):
    __tablename__ = 'solutions'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # e.g., 'Accepted', 'Wrong Answer', etc.
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=False)

    user = relationship('User', back_populates='solutions')
    problem = relationship('Problem', back_populates='solutions')

# Add back_populates in User and Problem classes if not already present
User.solutions = relationship('Solution', back_populates='user', cascade='all, delete-orphan')
Problem.solutions = relationship('Solution', back_populates='problem', cascade='all, delete-orphan')