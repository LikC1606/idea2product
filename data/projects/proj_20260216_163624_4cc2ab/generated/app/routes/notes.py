from flask import Blueprint, request, jsonify
from app import db
from app.models.note import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes])

@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note_by_id(note_id):
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    new_note = Note(title=data['title'], content=data['content'])
    db.session.add(new_note)
    db.session.commit()
    return jsonify(new_note.to_dict()), 201

@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    data = request.get_json()
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    db.session.commit()
    return jsonify(note.to_dict())

@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully.'})

@notes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('query', '')
    notes = Note.query.filter(
        (Note.title.ilike(f'%{query}%')) | (Note.content.ilike(f'%{query}%'))
    ).all()
    return jsonify([note.to_dict() for note in notes])