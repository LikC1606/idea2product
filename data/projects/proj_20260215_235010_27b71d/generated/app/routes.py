from flask import Blueprint, render_template, request, redirect, url_for
from app.models.note import Note
from app.database import db

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/', methods=['GET'])
def home():
    notes = Note.query.all()
    return render_template('index.html', notes=notes)

@notes_bp.route('/add', methods=['POST'])
def add_note():
    note_content = request.form.get('content')
    if note_content:
        new_note = Note(content=note_content)
        db.session.add(new_note)
        db.session.commit()
    return redirect(url_for('notes.home'))

@notes_bp.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return redirect(url_for('notes.home'))