from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Base for models
Base = declarative_base()

# Database configuration
DATABASE_URL = "sqlite:///app.db"  # Replace with your actual database URL

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Dependency for getting the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Exported items
__all__ = ["Base", "engine", "SessionLocal", "get_db"]