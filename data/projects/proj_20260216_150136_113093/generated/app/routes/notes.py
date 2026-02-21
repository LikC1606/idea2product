from flask import Blueprint, request, jsonify
from app import db
from app.models.note import Note
from datetime import datetime

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    
    if 'title' not in data or 'content' not in data or 'category' not in data:
        return jsonify({'error': 'Title, content, and category are required'}), 400

    note = Note(
        title=data['title'],
        content=data['content'],
        category=data['category'],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(note)
    db.session.commit()

    return jsonify(note.to_dict()), 201

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes])

@notes_bp.route('/notes/<int:id>', methods=['PUT'])
def update_note(id):
    note = Note.query.get_or_404(id)
    data = request.get_json()

    if 'title' not in data or 'content' not in data or 'category' not in data:
        return jsonify({'error': 'Title, content, and category are required'}), 400

    note.title = data['title']
    note.content = data['content']
    note.category = data['category']
    note.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify(note.to_dict())

@notes_bp.route('/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})