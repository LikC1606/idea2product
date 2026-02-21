from app.database import db
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    result = Column(String(20), nullable=False)
    submission_time = Column(db.DateTime, default=db.func.now(), nullable=False)

    user = relationship('User', back_populates='solutions')
    problem = relationship('Problem', back_populates='solutions')

    def __repr__(self):
        return f'<Solution {self.id} by User {self.user_id} for Problem {self.problem_id}>'