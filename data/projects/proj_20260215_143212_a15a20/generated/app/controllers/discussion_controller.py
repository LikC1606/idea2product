from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models.discussion import Discussion, Comment
from app.database import db_session

discussion_controller = Blueprint('discussion_controller', __name__)

@discussion_controller.route('/discussions', methods=['GET'])
def get_discussions():
    try:
        discussions = db_session.query(Discussion).all()
        return jsonify([discussion.to_dict() for discussion in discussions]), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@discussion_controller.route('/discussions/<int:discussion_id>', methods=['GET'])
def get_discussion(discussion_id):
    try:
        discussion = db_session.query(Discussion).filter_by(id=discussion_id).first()
        if discussion:
            return jsonify(discussion.to_dict()), 200
        else:
            return jsonify({"error": "Discussion not found"}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@discussion_controller.route('/discussions', methods=['POST'])
def create_discussion():
    try:
        data = request.json
        new_discussion = Discussion(title=data['title'], content=data['content'], user_id=data['user_id'])
        db_session.add(new_discussion)
        db_session.commit()
        return jsonify(new_discussion.to_dict()), 201
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

@discussion_controller.route('/discussions/<int:discussion_id>/comments', methods=['POST'])
def add_comment(discussion_id):
    try:
        data = request.json
        discussion = db_session.query(Discussion).filter_by(id=discussion_id).first()
        if discussion:
            new_comment = Comment(content=data['content'], user_id=data['user_id'], discussion_id=discussion_id)
            db_session.add(new_comment)
            db_session.commit()
            return jsonify(new_comment.to_dict()), 201
        else:
            return jsonify({"error": "Discussion not found"}), 404
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

@discussion_controller.route('/discussions/<int:discussion_id>/comments', methods=['GET'])
def get_comments(discussion_id):
    try:
        comments = db_session.query(Comment).filter_by(discussion_id=discussion_id).all()
        return jsonify([comment.to_dict() for comment in comments]), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500