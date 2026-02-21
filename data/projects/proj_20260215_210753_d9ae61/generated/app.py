from flask import Flask
from app.database import db
from app import create_app
from app.routes import register_routes

# Create the Flask application instance
app = create_app()

# Register all blueprints
register_routes(app)

# Run the application
if __name__ == "__main__":
    app.run(debug=True)