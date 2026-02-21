from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        from app.models import Note
        db.create_all()

    from app.routes import notes_bp
    app.register_blueprint(notes_bp)

    return app

`app/models.py`
from app import db

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }

`app/routes.py`
from flask import Blueprint, request, jsonify
from app import db
from app.models import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Invalid input"}), 400

    new_note = Note(content=data['content'])
    db.session.add(new_note)
    db.session.commit()

    return jsonify(new_note.to_dict()), 201

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes]), 200

`app/__init__.py`
from app import create_app, db
from app.models import Note