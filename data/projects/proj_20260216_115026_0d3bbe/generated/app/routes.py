from flask import Blueprint, request, jsonify
from app.models.note import Note
from app import db

bp = Blueprint('routes', __name__)

@bp.route('/api/notes', methods=['POST'])
def save_note():
    data = request.get_json()
    content = data.get('content')

    if not content or not content.strip():
        return jsonify({'error': 'Note content cannot be empty'}), 400

    new_note = Note(content=content)
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'message': 'Note saved successfully', 'note': {'id': new_note.id, 'content': new_note.content}}), 201

@bp.route('/api/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    notes_list = [{'id': note.id, 'content': note.content} for note in notes]

    return jsonify({'notes': notes_list}), 200