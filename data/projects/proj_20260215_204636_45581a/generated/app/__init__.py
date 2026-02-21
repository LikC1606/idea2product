from flask import Flask, render_template
from app.database import db
from app.routes import register_routes

def create_app():
    # Create Flask application
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Configure the app (update with your actual configuration)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register routes and blueprints
    register_routes(app)

    # Define home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app