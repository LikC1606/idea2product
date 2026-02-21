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
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    note = Note(content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    note.content = content
    db.session.commit()
    return jsonify(note.to_dict())

@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})

@notes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    notes = Note.query.filter(Note.content.ilike(f'%{query}%')).all()
    return jsonify([note.to_dict() for note in notes])