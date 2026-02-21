from sqlalchemy import orm

# Configure SQLAlchemy ORM settings
session_factory = orm.sessionmaker()
Session = orm.scoped_session(session_factory)