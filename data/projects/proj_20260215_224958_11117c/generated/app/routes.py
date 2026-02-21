from flask import Blueprint, request, jsonify
from app.models import Note
from app import db

notes_bp = Blueprint('notes', __name__)

# Route to create a new note
@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    title = data.get('title', '')
    content = data.get('content', '')
    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400
    new_note = Note(title=title, content=content)
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully', 'note': new_note.to_dict()}), 201

# Route to get all notes
@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes]), 200

# Route to get a specific note by ID
@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note.to_dict()), 200

# Route to update a note by ID
@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    title = data.get('title', note.title)
    content = data.get('content', note.content)
    note.title = title
    note.content = content
    db.session.commit()
    return jsonify({'message': 'Note updated successfully', 'note': note.to_dict()}), 200

# Route to delete a note by ID
@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'}), 200