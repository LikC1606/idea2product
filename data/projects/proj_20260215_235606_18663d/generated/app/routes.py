from flask import Blueprint, render_template, request, redirect
from app.models.note import Note
from app.database import db

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/', methods=['GET'])
def index():
    notes = Note.query.all()
    return render_template('index.html', notes=notes)

@notes_bp.route('/add', methods=['POST'])
def add_note():
    content = request.form.get('content')
    if content:
        new_note = Note(content=content)
        db.session.add(new_note)
        db.session.commit()
    return redirect('/')