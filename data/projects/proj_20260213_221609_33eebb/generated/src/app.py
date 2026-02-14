from flask import Flask
from src.routes import setup_routes
from src.database import initialize_db

def create_app():
    app = Flask(__name__)
    
    # Initialize database
    initialize_db(app)
    
    # Setup routes
    setup_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)