from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Base class for the database models
Base = declarative_base()

# User table
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with ProductDescription
    descriptions = relationship('ProductDescription', back_populates='user')

# Product Description table
class ProductDescription(Base):
    __tablename__ = 'product_descriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    image_path = Column(String(255), nullable=False)
    input_text = Column(Text, nullable=True)
    generated_title = Column(String(255), nullable=False)
    generated_points = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with User
    user = relationship('User', back_populates='descriptions')

# Database setup
def init_db(database_url):
    """
    Initializes the database, creates tables, and returns a session factory.
    
    :param database_url: Database connection URL
    :return: Session factory
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    return SessionFactory