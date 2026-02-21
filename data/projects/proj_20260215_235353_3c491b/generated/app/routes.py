from flask import Blueprint, render_template, request, redirect, url_for
from app.models.note import Note
from app.database import db

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/')
def index():
    # Fetch all notes from the database
    notes = Note.query.all()
    return render_template('index.html', notes=notes)

@notes_bp.route('/add', methods=['POST'])
def add_note():
    # Get the note text from the form
    note_text = request.form.get('note_text')
    
    if note_text:
        # Create a new Note object and save it to the database
        new_note = Note(content=note_text)
        db.session.add(new_note)
        db.session.commit()
    
    return redirect(url_for('notes.index'))

@notes_bp.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    # Find the note by ID and delete it from the database
    note_to_delete = Note.query.get(note_id)
    
    if note_to_delete:
        db.session.delete(note_to_delete)
        db.session.commit()
    
    return redirect(url_for('notes.index'))