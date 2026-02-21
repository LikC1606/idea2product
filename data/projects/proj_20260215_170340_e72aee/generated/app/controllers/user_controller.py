from flask import Blueprint, jsonify, request
from app.models.user import User
from app.database import db

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        users = User.query.all()
        user_list = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
        return jsonify(user_list), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user = User.query.get(user_id)
        if user:
            user_data = {'id': user.id, 'username': user.username, 'email': user.email}
            return jsonify(user_data), 200
        return jsonify({'error': 'User not found'}), 404

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        if not data or not all(key in data for key in ('username', 'email', 'password')):
            return jsonify({'error': 'Invalid input'}), 400

        new_user = User(username=data['username'], email=data['email'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'id': new_user.id}), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400

        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.password = data.get('password', user.password)
        db.session.commit()
        return jsonify({'message': 'User updated successfully'}), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200

    return user_bp