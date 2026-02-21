from flask import Blueprint, request, jsonify
from app.models import db, Note

routes = Blueprint('routes', __name__)

@routes.route('/notes', methods=['POST'])
def create_note():
    data = request.json
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    note = Note(title=data['title'], content=data['content'])
    db.session.add(note)
    db.session.commit()
    return jsonify({'id': note.id, 'title': note.title, 'content': note.content}), 201

@routes.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([{'id': note.id, 'title': note.title, 'content': note.content} for note in notes]), 200

@routes.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    notes = Note.query.filter(Note.title.contains(query) | Note.content.contains(query)).all()
    return jsonify([{'id': note.id, 'title': note.title, 'content': note.content} for note in notes]), 200