from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Base class for SQLAlchemy models
Base = declarative_base()

# Database connection setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")  # Default to SQLite if no env var is set
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Example User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

# Example Problem model
class Problem(Base):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', back_populates='problems')

# Example Submission model
class Submission(Base):
    __tablename__ = 'submissions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=False)
    code = Column(Text, nullable=False)
    result = Column(String, nullable=False)
    submitted_at = Column(DateTime, nullable=False)

    user = relationship('User', back_populates='submissions')
    problem = relationship('Problem', back_populates='submissions')

# Relationships
User.problems = relationship('Problem', back_populates='creator', cascade='all, delete-orphan')
User.submissions = relationship('Submission', back_populates='user', cascade='all, delete-orphan')
Problem.submissions = relationship('Submission', back_populates='problem', cascade='all, delete-orphan')

# Function to create the database tables
def init_db():
    Base.metadata.create_all(bind=engine)
# SQLAlchemy db instance for models
db = SQLAlchemy()
