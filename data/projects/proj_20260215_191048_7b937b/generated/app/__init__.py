from flask import Flask, render_template
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')
    
    # Configure the app (e.g., add secret key or other settings if needed)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database with the app
    db.init_app(app)

    # Register blueprints with the app
    register_blueprints(app)

    # Default route for the application
    @app.route('/')
    def home():
        return render_template('index.html')

    return app