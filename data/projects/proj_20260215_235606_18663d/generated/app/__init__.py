from flask import Flask
from app.database import db
from app.routes import notes_bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'

    db.init_app(app)

    app.register_blueprint(notes_bp)

    @app.route('/')
    def home():
        return "Welcome to the Simple Note-Taking App!"

    with app.app_context():
        db.create_all()

    return app