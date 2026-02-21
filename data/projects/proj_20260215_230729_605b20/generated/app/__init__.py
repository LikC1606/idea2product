from flask import Flask, render_template
from app.database import db
from app.routes import notes_bp

# Import models for db.create_all()
from app.models.note import Note


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(notes_bp)

    # Define home route
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
