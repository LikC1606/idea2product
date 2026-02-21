# Required Imports
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, User

# Must Export
user_bp = Blueprint('user', __name__)

# Routes
@user_bp.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        users_list = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
        return jsonify(users_list), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user_data = {'id': user.id, 'username': user.username, 'email': user.email}
        return jsonify(user_data), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        new_user = User(username=data['username'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'user_id': new_user.id}), 201
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        data = request.json
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        db.session.commit()
        return jsonify({'message': 'User updated successfully'}), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500