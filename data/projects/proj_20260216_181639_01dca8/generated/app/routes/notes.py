from flask import Blueprint, request, jsonify
from app import db
from app.models.note import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes])

@notes_bp.route('/notes/<int:id>', methods=['GET'])
def get_note(id):
    note = Note.query.get_or_404(id)
    return jsonify(note.to_dict())

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    note = Note(title=title, content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@notes_bp.route('/notes/<int:id>', methods=['PUT'])
def update_note(id):
    note = Note.query.get_or_404(id)
    data = request.get_json()

    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    note.title = title
    note.content = content
    db.session.commit()
    return jsonify(note.to_dict())

@notes_bp.route('/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})

@notes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('query')

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    notes = Note.query.filter(
        (Note.title.ilike(f'%{query}%')) | (Note.content.ilike(f'%{query}%'))
    ).all()
    return jsonify([note.to_dict() for note in notes])