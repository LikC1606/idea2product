from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db_session
from app.models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all users"""
    try:
        session = get_db_session()
        users = session.query(User).all()
        user_list = [user.to_dict() for user in users]
        return jsonify(user_list), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a user by ID"""
    try:
        session = get_db_session()
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        session = get_db_session()
        data = request.get_json()
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({"error": "Invalid input"}), 400

        user = User(name=data['name'], email=data['email'])
        session.add(user)
        session.commit()
        return jsonify(user.to_dict()), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user"""
    try:
        session = get_db_session()
        data = request.get_json()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        
        session.commit()
        return jsonify(user.to_dict()), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user by ID"""
    try:
        session = get_db_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        session.delete(user)
        session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500