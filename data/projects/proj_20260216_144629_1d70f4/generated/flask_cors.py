# flask_cors.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    CORS(app)

    from app.models import Note

    with app.app_context():
        db.create_all()

    from app.routes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/notes')

    return app