# app/routes.py
from flask import Blueprint, request, jsonify
from app.models import db, Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    new_note = Note(text=data['text'])
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'id': new_note.id, 'text': new_note.text}), 201

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    notes_list = [{'id': note.id, 'text': note.text} for note in notes]
    return jsonify(notes_list), 200

# app/models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)

# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.models import db
from app.routes import notes_bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(notes_bp, url_prefix='/api')

    return app

# app.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)