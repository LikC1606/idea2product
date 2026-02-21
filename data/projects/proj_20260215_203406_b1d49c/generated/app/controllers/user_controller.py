from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_all_users():
    """Fetch all users."""
    db = get_db()
    try:
        users = db.query(User).all()
        return jsonify([user.to_dict() for user in users]), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Fetch a specific user by ID."""
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    db = get_db()
    data = request.get_json()
    try:
        new_user = User(**data)
        db.add(new_user)
        db.commit()
        return jsonify(new_user.to_dict()), 201
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user's information."""
    db = get_db()
    data = request.get_json()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in data.items():
                setattr(user, key, value)
            db.commit()
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user by ID."""
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500