# app/routes/user_routes.py

from flask import Blueprint, request, jsonify
from app.models import User  # Assuming this is the SQLAlchemy model for users
from app.database import db  # Assuming this is the database instance
from sqlalchemy.exc import SQLAlchemyError

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    """
    Get a list of all users.
    """
    try:
        users = User.query.all()
        users_list = [user.to_dict() for user in users]  # Assuming User model has a `to_dict` method
        return jsonify(users_list), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a single user by ID.
    """
    try:
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user.
    """
    try:
        data = request.get_json()
        new_user = User(**data)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update an existing user.
    """
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        for key, value in data.items():
            setattr(user, key, value)
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.
    """
    try:
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500