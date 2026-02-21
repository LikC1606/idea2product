from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# initialize the SQLAlchemy object
db = SQLAlchemy()

def setup_database(app):
    # Configure database URI, adapt this to your specific database setup
    database_uri = 'sqlite:///acm_problem_solving_platform.db'  # Example for SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Bind SQLAlchemy to the Flask app
    db.init_app(app)

    # Create engine and session
    engine = create_engine(database_uri)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    # Return the session object for use in application
    return Session

# SQLAlchemy db instance for models
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
