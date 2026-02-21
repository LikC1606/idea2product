from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import Note

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/notes', methods=['POST'])
def create_note():
    """Route to create a new note"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

        if not title or not content:
            return jsonify({'error': 'Title and content are required'}), 400

        new_note = Note(title=title, content=content)
        db.session.add(new_note)
        db.session.commit()

        return jsonify({'message': 'Note created successfully', 'note': new_note.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes_bp.route('/notes', methods=['GET'])
def get_all_notes():
    """Route to get all notes"""
    try:
        notes = Note.query.all()
        notes_list = [note.to_dict() for note in notes]
        return jsonify({'notes': notes_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note_by_id(note_id):
    """Route to get a single note by its ID"""
    try:
        note = Note.query.get(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        return jsonify({'note': note.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Route to search notes by title"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400

        results = Note.query.filter(Note.title.ilike(f'%{query}%')).all()
        if not results:
            return jsonify({'message': 'No notes found'}), 404

        result_list = [note.to_dict() for note in results]
        return jsonify({'results': result_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Route to delete a note by its ID"""
    try:
        note = Note.query.get(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404

        db.session.delete(note)
        db.session.commit()

        return jsonify({'message': 'Note deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Route to update a note by its ID"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

        note = Note.query.get(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404

        if title:
            note.title = title
        if content:
            note.content = content

        db.session.commit()

        return jsonify({'message': 'Note updated successfully', 'note': note.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500