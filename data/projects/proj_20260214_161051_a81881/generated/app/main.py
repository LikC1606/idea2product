from flask import Flask
from app.routes import initialize_routes
from app.models import initialize_models

def create_app():
    app = Flask(__name__)

    # Initialize models and routes
    initialize_models(app)
    initialize_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)