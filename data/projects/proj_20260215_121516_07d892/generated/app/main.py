from flask import Flask
from app.routes import register_routes
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register application routes
    register_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)