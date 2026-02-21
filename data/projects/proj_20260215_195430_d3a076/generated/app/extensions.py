from flask_migrate import Migrate

def migrate():
    """
    Initializes Flask-Migrate with the Flask app and SQLAlchemy database instance.
    """
    from app.database import db
    from app import create_app

    app = create_app()
    Migrate(app, db)