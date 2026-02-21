from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.database import db_session

user_controller = Blueprint('user_controller', __name__)

@user_controller.route('/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    try:
        user = db_session.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_controller.route('/users', methods=['POST'])
def create_user_profile():
    data = request.json
    try:
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password')  # Assume password is hashed before saving
        )
        db_session.add(new_user)
        db_session.commit()
        return jsonify(new_user.to_dict()), 201
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@user_controller.route('/users/<int:user_id>', methods=['PUT'])
def update_user_profile(user_id):
    data = request.json
    try:
        user = db_session.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        if data.get('password'):
            user.password = data.get('password')  # Assume password is hashed before saving
        db_session.commit()
        return jsonify(user.to_dict()), 200
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@user_controller.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user_profile(user_id):
    try:
        user = db_session.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        db_session.delete(user)
        db_session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500