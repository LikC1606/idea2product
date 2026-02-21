from flask import Blueprint, request, jsonify
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        """
        Fetch all users
        """
        users = User.query.all()
        users_data = [user.to_dict() for user in users]
        return jsonify(users_data), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        """
        Fetch a single user by ID
        """
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        """
        Create a new user
        """
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        try:
            new_user = User(**data)
            db.session.add(new_user)
            db.session.commit()
            return jsonify(new_user.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        """
        Update an existing user
        """
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        try:
            for key, value in data.items():
                setattr(user, key, value)
            db.session.add(user)
            db.session.commit()
            return jsonify(user.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        """
        Delete a user by ID
        """
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return user_bp