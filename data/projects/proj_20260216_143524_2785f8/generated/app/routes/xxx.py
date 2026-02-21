# app/routes/xxx.py

from flask import Blueprint, request, jsonify
from app.models import db, Note

xxx_bp = Blueprint('xxx', __name__)

# Route to create a new note
@xxx_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    new_note = Note(title=title, content=content)
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'message': 'Note created successfully', 'note': new_note.to_dict()}), 201

# Route to get all notes
@xxx_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes]), 200

# Route to search notes by title or content
@xxx_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    results = Note.query.filter(
        (Note.title.ilike(f'%{query}%')) | (Note.content.ilike(f'%{query}%'))
    ).all()

    return jsonify([note.to_dict() for note in results]), 200

# Route to organize notes (e.g., by title)
@xxx_bp.route('/notes/organize', methods=['GET'])
def organize_notes():
    order_by = request.args.get('order_by', 'title')
    if order_by not in ['title', 'created_at']:
        return jsonify({'error': 'Invalid order_by value'}), 400

    if order_by == 'title':
        notes = Note.query.order_by(Note.title).all()
    else:
        notes = Note.query.order_by(Note.created_at).all()

    return jsonify([note.to_dict() for note in notes]), 200