from flask import Blueprint, request, jsonify
from app.models.comment import Comment
from app import db

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/comments/<int:post_id>', methods=['GET'])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).all()
    return jsonify([comment.to_dict() for comment in comments])

@comments_bp.route('/comments', methods=['POST'])
def add_comment():
    data = request.get_json()
    new_comment = Comment(
        post_id=data['post_id'],
        content=data['content']
    )
    db.session.add(new_comment)
    db.session.commit()
    return jsonify(new_comment.to_dict()), 201