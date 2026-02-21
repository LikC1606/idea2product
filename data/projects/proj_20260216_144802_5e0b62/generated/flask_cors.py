# flask_cors.py

from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

# Models
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)

# Blueprints
notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['POST'])
def create_note():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    category = data.get('category', None)

    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    new_note = Note(title=title, content=content, category=category)
    db.session.add(new_note)
    db.session.commit()

    return jsonify({"id": new_note.id, "title": new_note.title, "content": new_note.content, "category": new_note.category}), 201

@notes_bp.route('/notes', methods=['GET'])
def get_notes():
    category = request.args.get('category')
    query = Note.query
    if category:
        query = query.filter_by(category=category)
    
    notes = query.all()
    return jsonify([{"id": note.id, "title": note.title, "content": note.content, "category": note.category} for note in notes])

@notes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    keyword = request.args.get('q')
    if not keyword:
        return jsonify({"error": "Search query is required"}), 400

    notes = Note.query.filter((Note.title.ilike(f"%{keyword}%")) | (Note.content.ilike(f"%{keyword}%"))).all()
    return jsonify([{"id": note.id, "title": note.title, "content": note.content, "category": note.category} for note in notes])

# App Factory
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    CORS(app)

    with app.app_context():
        from flask_cors import db
        db.create_all()

    app.register_blueprint(notes_bp, url_prefix='/api')
    return app