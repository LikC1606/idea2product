from flask import Flask, render_template
from app.database import db
from app.routes import register_routes

def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
        static_url_path='/static'
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Example database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register routes
    register_routes(app)

    # Home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app