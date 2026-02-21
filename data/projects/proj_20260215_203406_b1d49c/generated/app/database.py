# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base layer for database models
Base = declarative_base()

# SQLAlchemy database connection setup
DATABASE_URL = "sqlite:///acm_platform.db"  # Replace with your actual database URL

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()