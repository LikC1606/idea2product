from flask import Blueprint, request, jsonify
from app import db
from app.models.note import Note

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    note = Note(title=data['title'], content=data['content'])
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@note_bp.route('/notes/<int:id>', methods=['GET'])
def get_note(id):
    note = Note.query.get_or_404(id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:id>', methods=['PUT'])
def update_note(id):
    data = request.get_json()
    note = Note.query.get_or_404(id)
    note.title = data['title']
    note.content = data['content']
    db.session.commit()
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    notes = Note.query.filter(Note.title.like(f'%{query}%')).all()
    return jsonify([note.to_dict() for note in notes])