from flask import Blueprint, request, jsonify
from app.models.comment import Comment
from app import db

comment_bp = Blueprint('comments', __name__)

@comment_bp.route('/', methods=['POST'])
def add_comment():
    data = request.get_json()
    blog_id = data.get('blog_id')
    content = data.get('content')
    author = data.get('author')

    if not blog_id or not content or not author:
        return jsonify({'error': 'Missing required fields'}), 400

    comment = Comment(blog_id=blog_id, content=content, author=author)
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_dict()), 201

@comment_bp.route('/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'Comment deleted successfully'}), 200

@comment_bp.route('/<int:blog_id>', methods=['GET'])
def get_comments(blog_id):
    comments = Comment.query.filter_by(blog_id=blog_id).all()
    return jsonify([comment.to_dict() for comment in comments]), 200