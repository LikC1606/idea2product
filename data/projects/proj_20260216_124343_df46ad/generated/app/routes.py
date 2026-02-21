from flask import Blueprint, request, jsonify
from app.models.note import Note
from app.database import db

routes_blueprint = Blueprint('routes', __name__)

@routes_blueprint.route('/notes', methods=['POST'])
def save_note():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400

    new_note = Note(content=data['content'])
    db.session.add(new_note)
    db.session.commit()

    return jsonify({
        'id': new_note.id,
        'content': new_note.content,
        'created_at': new_note.created_at
    }), 201

@routes_blueprint.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    notes_list = [
        {'id': note.id, 'content': note.content, 'created_at': note.created_at}
        for note in notes
    ]
    return jsonify(notes_list), 200