from flask import Blueprint, jsonify, request
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user = User.query.get(user_id)
        if user:
            return jsonify(user.to_dict()), 200
        return jsonify({'error': 'User not found'}), 404

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        user = User(**data)
        try:
            user.save()
            return jsonify(user.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        data = request.get_json()
        try:
            for key, value in data.items():
                setattr(user, key, value)
            user.save()
            return jsonify(user.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        try:
            user.delete()
            return jsonify({'message': f'User {user_id} deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return user_bp