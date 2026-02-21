from flask import Blueprint, request, redirect, render_template
from app.database import db
from app.models.note import Note

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/save-note', methods=['POST'])
def save_note():
    note_content = request.form.get('note')
    if note_content:
        new_note = Note(content=note_content)
        db.session.add(new_note)
        db.session.commit()
    return redirect('/')