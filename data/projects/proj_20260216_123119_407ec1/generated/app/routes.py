from flask import Blueprint, request, jsonify
from app.database import db
from app.models.note import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    note = Note(content=data['content'])
    db.session.add(note)
    db.session.commit()

    return jsonify({'id': note.id, 'content': note.content, 'created_at': note.created_at}), 201

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    notes_list = [{'id': note.id, 'content': note.content, 'created_at': note.created_at} for note in notes]
    return jsonify(notes_list), 200