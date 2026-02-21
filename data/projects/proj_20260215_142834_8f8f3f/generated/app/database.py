from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

# Base declarative class
Base = declarative_base()

# Database URL (could be set using environment variables for security reasons)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///acm_problem_solving.db')

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Initialize the database connection
def init_db():
    import app.models  # Import models to register them with Base
    Base.metadata.create_all(bind=engine)

# Dependency to get the session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()