from flask import Blueprint, request, jsonify
from app.models import db, Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"error": "Invalid input"}), 400

    new_note = Note(title=data['title'], content=data['content'])
    db.session.add(new_note)
    db.session.commit()
    return jsonify({"message": "Note created", "note": {"id": new_note.id, "title": new_note.title, "content": new_note.content}}), 201

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    result = [{"id": note.id, "title": note.title, "content": note.content} for note in notes]
    return jsonify(result), 200

@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"id": note.id, "title": note.title, "content": note.content}), 200

@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"error": "Invalid input"}), 400

    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404

    note.title = data['title']
    note.content = data['content']
    db.session.commit()
    return jsonify({"message": "Note updated", "note": {"id": note.id, "title": note.title, "content": note.content}}), 200

@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted"}), 200