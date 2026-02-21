# app/routes/xxx.py

from flask import Blueprint, request, jsonify
from app.models import Note
from app import db

xxx_bp = Blueprint('xxx', __name__)

@xxx_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    new_note = Note(title=data['title'], content=data['content'])
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'id': new_note.id, 'title': new_note.title, 'content': new_note.content}), 201

@xxx_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    notes_list = [{'id': note.id, 'title': note.title, 'content': note.content} for note in notes]
    return jsonify(notes_list), 200

@xxx_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    notes = Note.query.filter(Note.title.contains(query) | Note.content.contains(query)).all()
    notes_list = [{'id': note.id, 'title': note.title, 'content': note.content} for note in notes]

    return jsonify(notes_list), 200

@xxx_bp.route('/notes/organize', methods=['GET'])
def organize_notes():
    notes = Note.query.order_by(Note.title.asc()).all()
    notes_list = [{'id': note.id, 'title': note.title, 'content': note.content} for note in notes]
    return jsonify(notes_list), 200