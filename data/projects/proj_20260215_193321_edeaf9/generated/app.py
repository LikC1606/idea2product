from flask import Flask
from app.routes import register_blueprints
from app.database import db
from app import create_app

# Initialize the Flask application
app = create_app()

# Register blueprints
register_blueprints(app)

# Database initialization
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)