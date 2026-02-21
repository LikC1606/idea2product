from flask import Blueprint, request, jsonify
from app import db
from app.models.note import Note

notes_bp = Blueprint('notes', __name__)


@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    """获取所有笔记"""
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])


@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """获取单个笔记"""
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note.to_dict())


@notes_bp.route('/notes', methods=['POST'])
def create_note():
    """创建笔记"""
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400

    content = data['content'].strip()
    if not content:
        return jsonify({'error': 'Content cannot be empty'}), 400

    note = Note(content=content)
    db.session.add(note)
    db.session.commit()

    return jsonify(note.to_dict()), 201


@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """更新笔记"""
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    data = request.get_json()
    if 'content' in data:
        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'Content cannot be empty'}), 400
        note.content = content

    db.session.commit()
    return jsonify(note.to_dict())


@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """删除笔记"""
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    db.session.delete(note)
    db.session.commit()

    return jsonify({'message': 'Note deleted'}), 200
