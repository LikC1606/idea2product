# app/routes/xxx.py
from flask import Blueprint, request, jsonify
from app.models import Note, db

xxx_bp = Blueprint('xxx', __name__, url_prefix='/notes')

@xxx_bp.route('', methods=['POST'])
def create_note():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    note = Note(title=title, content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully', 'note': note.to_dict()}), 201

@xxx_bp.route('', methods=['GET'])
def list_notes():
    notes = Note.query.all()
    return jsonify({'notes': [note.to_dict() for note in notes]}), 200

@xxx_bp.route('/<int:note_id>', methods=['GET'])
def get_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify({'note': note.to_dict()}), 200

@xxx_bp.route('/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    if title:
        note.title = title
    if content:
        note.content = content

    db.session.commit()
    return jsonify({'message': 'Note updated successfully', 'note': note.to_dict()}), 200

@xxx_bp.route('/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'}), 200

@xxx_bp.route('/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    notes = Note.query.filter(Note.title.ilike(f'%{query}%') | Note.content.ilike(f'%{query}%')).all()
    return jsonify({'notes': [note.to_dict() for note in notes]}), 200