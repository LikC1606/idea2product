from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import db
from app.models.problem import Problem

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    language = Column(String, nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=False)
    user_id = Column(Integer, nullable=False)  # Assuming a User model exists

    problem = relationship('Problem', back_populates='solutions')

# Establishing reverse relationship in the Problem model
Problem.solutions = relationship('Solution', back_populates='problem', cascade='all, delete-orphan')