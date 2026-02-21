from app.database import db
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    problems_solved = relationship('Problem', backref='solver', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'