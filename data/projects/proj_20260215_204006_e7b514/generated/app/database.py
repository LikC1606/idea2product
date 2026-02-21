from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Database configuration
DATABASE_URL = "sqlite:///acm_platform.db"  # Example database URL, replace with your actual database connection string

# SQLAlchemy engine and session setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """Initialize the database with SQLAlchemy models."""
    db.metadata.create_all(bind=engine)

def get_db_session():
    """Provide a scoped session for database operations."""
    try:
        session = SessionLocal()
        yield session
    finally:
        session.close()