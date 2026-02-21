from flask import Blueprint, request, render_template, redirect, url_for, flash
from app import db
from app.models import Note

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    notes = Note.query.all()
    return render_template('index.html', notes=notes)

@routes.route('/create', methods=['GET', 'POST'])
def create_note():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash('Title and content cannot be empty', 'error')
            return render_template('create.html')
        
        new_note = Note(title=title, content=content)
        db.session.add(new_note)
        db.session.commit()
        flash('Note created successfully!', 'success')
        return redirect(url_for('routes.index'))
    
    return render_template('create.html')

@routes.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        
        if not note.title or not note.content:
            flash('Title and content cannot be empty', 'error')
            return render_template('edit.html', note=note)
        
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('routes.index'))
    
    return render_template('edit.html', note=note)

@routes.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('routes.index'))

@routes.route('/organize', methods=['GET', 'POST'])
def organize_notes():
    notes = Note.query.order_by(Note.title.asc()).all()  # Example organization by title
    return render_template('organize.html', notes=notes)