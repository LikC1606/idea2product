from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models.note import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    note = Note(content=data['content'])
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@notes_bp.route('/notes.html', methods=['GET'])
def notes_page():
    return render_template('notes.html')