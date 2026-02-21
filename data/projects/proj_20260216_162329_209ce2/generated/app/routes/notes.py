from flask import Blueprint, request, jsonify
from app import db
from app.models.note import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes])

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if 'content' not in data:
        return jsonify({'error': 'Content field is required'}), 400

    note = Note(content=data['content'])
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201
