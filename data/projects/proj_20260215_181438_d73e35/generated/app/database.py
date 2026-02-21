from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///app.db')
Session = sessionmaker(bind=engine)
db = scoped_session(Session)