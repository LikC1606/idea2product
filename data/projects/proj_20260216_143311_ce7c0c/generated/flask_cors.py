# flask_cors.py
from flask import Flask, jsonify, request, Blueprint
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
    new_note = Note(
        title=data.get('title'),
        content=data.get('content'),
        category=data.get('category', None)
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify({"message": "Note created successfully!", "note": {
        "id": new_note.id,
        "title": new_note.title,
        "content": new_note.content,
        "category": new_note.category
    }}), 201

@notes_bp.route('/notes', methods=['GET'])
def get_all_notes():
    category = request.args.get('category', None)
    if category:
        notes = Note.query.filter_by(category=category).all()
    else:
        notes = Note.query.all()
    notes_list = [{"id": note.id, "title": note.title, "content": note.content, "category": note.category} for note in notes]
    return jsonify(notes_list), 200

@notes_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('query', '')
    notes = Note.query.filter(
        (Note.title.contains(query)) | 
        (Note.content.contains(query))
    ).all()
    notes_list = [{"id": note.id, "title": note.title, "content": note.content, "category": note.category} for note in notes]
    return jsonify(notes_list), 200

# Application Factory
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(notes_bp, url_prefix='/api')

    return app

# Entry point
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)