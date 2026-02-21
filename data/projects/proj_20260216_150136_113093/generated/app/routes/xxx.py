from flask import Blueprint, request, jsonify
from app.models import db, Note

xxx = Blueprint('xxx', __name__)

@xxx.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({"error": "Invalid data"}), 400
    note = Note(title=data['title'], content=data['content'])
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@xxx.route('/notes/<int:note_id>', methods=['PUT'])
def edit_note(note_id):
    data = request.get_json()
    if not data or ('title' not in data and 'content' not in data):
        return jsonify({"error": "Invalid data"}), 400
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    if 'title' in data:
        note.title = data['title']
    if 'content' in data:
        note.content = data['content']
    db.session.commit()
    return jsonify(note.to_dict()), 200

@xxx.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted"}), 200

@xxx.route('/notes', methods=['GET'])
def organize_notes():
    notes = Note.query.all()
    organized_notes = [note.to_dict() for note in notes]
    return jsonify(organized_notes), 200