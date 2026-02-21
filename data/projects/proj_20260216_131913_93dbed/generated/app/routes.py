from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

db.create_all()

# Routes
@app.route('/')
def index():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('index.html', notes=notes)

@app.route('/create_note')
def create_note():
    return render_template('create_note.html')

@app.route('/create_note_action', methods=['POST'])
def create_note_action():
    content = request.form.get('content')
    if content:
        new_note = Note(content=content)
        db.session.add(new_note)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/notes', methods=['POST'])
def create_note_api():
    data = request.get_json()
    content = data.get('content', '')
    if content:
        new_note = Note(content=content)
        db.session.add(new_note)
        db.session.commit()
        return jsonify({'id': new_note.id, 'content': new_note.content, 'created_at': new_note.created_at}), 201
    return jsonify({'error': 'Content is required'}), 400

@app.route('/notes', methods=['GET'])
def get_notes_api():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return jsonify([{'id': note.id, 'content': note.content, 'created_at': note.created_at} for note in notes])

@app.route('/notes/search', methods=['GET'])
def search_notes_api():
    query = request.args.get('query', '')
    if query:
        results = Note.query.filter(Note.content.contains(query)).all()
        return jsonify([{'id': note.id, 'content': note.content, 'created_at': note.created_at} for note in results])
    return jsonify([])

@app.route('/search_notes', methods=['GET'])
def search_notes():
    query = request.args.get('query', '')
    results = []
    if query:
        results = Note.query.filter(Note.content.contains(query)).all()
    return render_template('search_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)