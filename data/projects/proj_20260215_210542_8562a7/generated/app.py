from flask import Flask
from app.database import db
from app.routes import register_routes

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy
    db.init_app(app)

    # Register routes
    register_routes(app)

    @app.route('/')
    def home():
        return app.send_static_file('index.html')

    return app