from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String

# Define the base for declarative models
Base = declarative_base()

# Database configuration
DATABASE_URL = "sqlite:///acm_problems.db"  # Example: SQLite database URL

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create the session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Example model for demonstration
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

# Function to initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)
# SQLAlchemy db instance for models
db = SQLAlchemy()
