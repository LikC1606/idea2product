from flask import Blueprint, jsonify, request
from app.models.user import User
from app.database import db

def user_bp():
    user_blueprint = Blueprint('user', __name__, url_prefix='/users')

    @user_blueprint.route('/', methods=['GET'])
    def get_users():
        users = User.query.all()
        users_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
        return jsonify(users_data), 200

    @user_blueprint.route('/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user_data = {'id': user.id, 'username': user.username, 'email': user.email}
        return jsonify(user_data), 200

    @user_blueprint.route('/', methods=['POST'])
    def create_user():
        data = request.get_json()
        if not data or 'username' not in data or 'email' not in data:
            return jsonify({'error': 'Invalid input'}), 400
        new_user = User(username=data['username'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'id': new_user.id}), 201

    @user_blueprint.route('/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        db.session.commit()
        return jsonify({'message': 'User updated successfully'}), 200

    @user_blueprint.route('/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200

    return user_blueprint