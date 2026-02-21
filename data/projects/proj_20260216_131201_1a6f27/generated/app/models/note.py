from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)