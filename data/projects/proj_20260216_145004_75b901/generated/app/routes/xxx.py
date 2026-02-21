# app/routes/xxx.py

from flask import Blueprint, request, jsonify
from app.models import db, Note

xxx_bp = Blueprint('xxx', __name__)

@xxx_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    new_note = Note(title=title, content=content)
    db.session.add(new_note)
    db.session.commit()

    return jsonify({"id": new_note.id, "title": new_note.title, "content": new_note.content}), 201

@xxx_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    notes_list = [{"id": note.id, "title": note.title, "content": note.content} for note in notes]
    return jsonify(notes_list), 200

@xxx_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify([]), 200

    notes = Note.query.filter(Note.title.ilike(f'%{query}%') | Note.content.ilike(f'%{query}%')).all()
    notes_list = [{"id": note.id, "title": note.title, "content": note.content} for note in notes]
    return jsonify(notes_list), 200