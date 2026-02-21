from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from app.database import db

# Configure the SQLAlchemy session
engine = create_engine('sqlite:///app.db')
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

# Function to get the scoped session
def get_session():
    return Session()

# Ensure the database tables are created
def init_db():
    db.create_all(bind=engine)