# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from app.models import Note  # Import models before db.create_all()
    with app.app_context():
        db.create_all()

    from app.routes import notes_bp
    app.register_blueprint(notes_bp)

    return app

# app/models.py
from app import db

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

# app/routes.py
from flask import Blueprint, request, jsonify
from app import db
from app.models import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400

    new_note = Note(content=data['content'])
    db.session.add(new_note)
    db.session.commit()
    return jsonify({"id": new_note.id, "content": new_note.content}), 201

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([{"id": note.id, "content": note.content} for note in notes]), 200

# app.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)