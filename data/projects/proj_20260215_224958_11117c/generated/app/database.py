from flask_sqlalchemy import SQLAlchemy
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL (SQLite for simplicity)
DATABASE_URL = "sqlite:///notes_app.db"

# Create the database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the declarative base class
Base = declarative_base()

# Export the interfaces
__all__ = ["engine", "SessionLocal", "Base"]
# SQLAlchemy db instance for models
db = SQLAlchemy()
