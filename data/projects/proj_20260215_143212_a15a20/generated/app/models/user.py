from app.database import db
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    solutions = relationship('Solution', backref='user', lazy=True)
    discussions = relationship('Discussion', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'