from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

# Database Configuration
DATABASE_URL = "sqlite:///acm_platform.db"  # Example database URL, replace as needed

# SQLAlchemy Engine and Session
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Function to initialize database
def init_db():
    import app.models  # Import models to ensure they're registered with metadata
    Base.metadata.create_all(bind=engine)
# SQLAlchemy db instance for models
db = SQLAlchemy()
