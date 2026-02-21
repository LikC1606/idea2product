from flask import Blueprint, render_template, request, redirect, url_for
from app.models.note import Note
from app.database import db

notes_bp = Blueprint('notes', __name__, template_folder='templates')

@notes_bp.route('/')
def index():
    notes = Note.query.all()  # Fetch all notes from the database
    return render_template('index.html', notes=notes)

@notes_bp.route('/add', methods=['POST'])
def add_note():
    note_content = request.form.get('content')  # Retrieve content from form input
    if note_content:
        new_note = Note(content=note_content)  # Create a new Note object
        db.session.add(new_note)  # Add the new note to the database session
        db.session.commit()  # Commit the changes to the database
    return redirect(url_for('notes.index'))  # Redirect back to the index page

@notes_bp.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get(note_id)  # Fetch the note by ID
    if note:
        db.session.delete(note)  # Delete the note from the database session
        db.session.commit()  # Commit the changes to the database
    return redirect(url_for('notes.index'))  # Redirect back to the index page