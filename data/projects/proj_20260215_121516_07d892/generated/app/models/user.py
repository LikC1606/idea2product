from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    solved_problems = Column(Integer, default=0)
    rank = Column(Integer, default=0)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', rank='{self.rank}')>"