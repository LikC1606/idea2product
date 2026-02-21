from flask import Blueprint, request, jsonify
from app.models.note import Note  # Assuming Note model is defined in app/models/note.py
from app.database import db

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    """Route to create a new note."""
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    title = data['title']
    content = data['content']

    note = Note(title=title, content=content)
    db.session.add(note)
    db.session.commit()

    return jsonify({'message': 'Note created successfully', 'note': note.to_dict()}), 201

@notes_bp.route('/notes', methods=['GET'])
def list_notes():
    """Route to list all notes."""
    notes = Note.query.all()
    notes_list = [note.to_dict() for note in notes]
    return jsonify({'notes': notes_list}), 200

@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Route to retrieve a specific note by ID."""
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    return jsonify({'note': note.to_dict()}), 200

@notes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Route to search notes by a query string."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No search query provided'}), 400

    results = Note.query.filter(Note.title.ilike(f'%{query}%') | Note.content.ilike(f'%{query}%')).all()
    results_list = [note.to_dict() for note in results]

    return jsonify({'results': results_list}), 200