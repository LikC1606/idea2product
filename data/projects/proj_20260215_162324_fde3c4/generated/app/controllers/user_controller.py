from flask import Blueprint, request, jsonify
from app.models.user import User
from app.database import db

user_controller = Blueprint('user_controller', __name__)

@user_controller.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        users_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
        return jsonify(users_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_controller.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user_data = {'id': user.id, 'username': user.username, 'email': user.email}
        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_controller.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        if not username or not email:
            return jsonify({'error': 'Invalid input'}), 400
        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'id': new_user.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_controller.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        username = data.get('username')
        email = data.get('email')
        if username:
            user.username = username
        if email:
            user.email = email
        db.session.commit()
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_controller.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500