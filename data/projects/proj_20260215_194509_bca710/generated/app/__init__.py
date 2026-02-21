from flask import Flask, render_template
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')
    
    # Configure the application (if necessary, add configurations here)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register blueprints for routes
    register_blueprints(app)

    # Define a default route for the application
    @app.route('/')
    def index():
        return render_template('index.html')

    return app