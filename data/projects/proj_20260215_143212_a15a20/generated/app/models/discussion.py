from app.database import db
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

class Discussion(db.Model):
    __tablename__ = 'discussions'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=False)

    user = relationship('User', back_populates='discussions')
    problem = relationship('Problem', back_populates='discussions')

    def __init__(self, title, content, user_id, problem_id):
        self.title = title
        self.content = content
        self.user_id = user_id
        self.problem_id = problem_id

    def __repr__(self):
        return f'<Discussion {self.title}>'