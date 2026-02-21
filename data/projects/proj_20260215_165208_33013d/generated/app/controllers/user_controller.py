from flask import Blueprint, jsonify, request
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    # Create a new user
    @user_bp.route('/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        try:
            new_user = User(**data)
            new_user.save()
            return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    # Retrieve all users
    @user_bp.route('/users', methods=['GET'])
    def get_users():
        try:
            users = User.query.all()
            return jsonify({'users': [user.to_dict() for user in users]}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Retrieve a specific user by ID
    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 404
            return jsonify({'user': user.to_dict()}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Update a user by ID
    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        data = request.get_json()
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 404
            for key, value in data.items():
                setattr(user, key, value)
            user.save()
            return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    # Delete a user by ID
    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 404
            user.delete()
            return jsonify({'message': 'User deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return user_bp