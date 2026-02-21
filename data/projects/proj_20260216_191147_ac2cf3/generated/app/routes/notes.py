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
    note = Note(content=data['content'])
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@notes_bp.route('/notes/<int:id>', methods=['PUT'])
def update_note(id):
    data = request.get_json()
    note = Note.query.get_or_404(id)
    note.content = data['content']
    db.session.commit()
    return jsonify(note.to_dict())

@notes_bp.route('/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})