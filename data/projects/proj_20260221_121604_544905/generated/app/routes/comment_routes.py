from flask import Blueprint, request, jsonify
from app.models.comment import Comment
from app import db

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/<int:blog_id>', methods=['GET'])
def get_comments(blog_id):
    """Retrieve all comments for a specific blog post."""
    comments = Comment.query.filter_by(blog_id=blog_id).all()
    return jsonify([comment.to_dict() for comment in comments])

@comments_bp.route('/', methods=['POST'])
def add_comment():
    """Add a comment to a specific blog post."""
    data = request.get_json()
    blog_id = data.get('blog_id')
    content = data.get('content')

    if not blog_id or not content:
        return jsonify({'error': 'Missing blog_id or content'}), 400

    comment = Comment(blog_id=blog_id, content=content)
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_dict()), 201