# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from app.models import Note
        db.create_all()

    from app.routes import notes_blueprint
    app.register_blueprint(notes_blueprint)

    return app

# app/models.py
from app import db

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

# app/routes.py
from flask import Blueprint, request, jsonify
from app.models import Note
from app import db

notes_blueprint = Blueprint('notes', __name__)

@notes_blueprint.route('/notes', methods=['POST'])
def save_note():
    data = request.get_json()
    content = data.get('content', '')

    if not content.strip():
        return jsonify({'error': 'Content cannot be empty'}), 400

    new_note = Note(content=content)
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'message': 'Note saved successfully', 'note': {'id': new_note.id, 'content': new_note.content}}), 201

@notes_blueprint.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    notes_data = [{'id': note.id, 'content': note.content} for note in notes]
    return jsonify(notes_data), 200

# app.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)