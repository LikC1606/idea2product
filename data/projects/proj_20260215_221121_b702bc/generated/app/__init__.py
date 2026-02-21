from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# Initialize the database instance
db = SQLAlchemy()

def create_app():
    # Initialize the Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'  # Example database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'your-secret-key'

    # Initialize extensions
    db.init_app(app)

    # Register blueprints (add specific blueprints here as needed)
    # from .routes import notes_bp
    # app.register_blueprint(notes_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Define the home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app