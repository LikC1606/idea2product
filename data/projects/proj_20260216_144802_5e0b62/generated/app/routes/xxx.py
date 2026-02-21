# app/routes/xxx.py

from flask import Blueprint, request, jsonify
from app.models import db, Note

xxx_bp = Blueprint('xxx', __name__)

@xxx_bp.route('/notes', methods=['POST'])
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

@xxx_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes])

@xxx_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    notes = Note.query.filter(Note.title.ilike(f'%{query}%') | Note.content.ilike(f'%{query}%')).all()
    return jsonify([note.to_dict() for note in notes])

@xxx_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})