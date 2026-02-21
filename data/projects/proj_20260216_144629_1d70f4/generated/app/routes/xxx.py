# app/routes/xxx.py

from flask import Blueprint, request, jsonify
from app.models import Note, db

xxx_bp = Blueprint('xxx', __name__)

@xxx_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    new_note = Note(title=data['title'], content=data['content'])
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully', 'note': new_note.to_dict()}), 201

@xxx_bp.route('/notes', methods=['GET'])
def get_all_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes]), 200

@xxx_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note_by_id(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note.to_dict()), 200

@xxx_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400

    notes = Note.query.filter(Note.title.contains(query) | Note.content.contains(query)).all()
    return jsonify([note.to_dict() for note in notes]), 200

@xxx_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    if not data or ('title' not in data and 'content' not in data):
        return jsonify({'error': 'Invalid input'}), 400

    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    if 'title' in data:
        note.title = data['title']
    if 'content' in data:
        note.content = data['content']

    db.session.commit()
    return jsonify({'message': 'Note updated successfully', 'note': note.to_dict()}), 200

@xxx_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'}), 200