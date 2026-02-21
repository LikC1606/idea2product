from flask import Blueprint, jsonify, request
from app.models.user import User
from app import db

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        try:
            users = User.query.all()
            user_list = [user.to_dict() for user in users]
            return jsonify(user_list), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        try:
            user = User.query.get(user_id)
            if user:
                return jsonify(user.to_dict()), 200
            else:
                return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        try:
            data = request.json
            new_user = User(**data)
            db.session.add(new_user)
            db.session.commit()
            return jsonify(new_user.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404

            data = request.json
            for key, value in data.items():
                setattr(user, key, value)
            db.session.add(user)
            db.session.commit()
            return jsonify(user.to_dict()), 200
        except Exception as e:
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
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return user_bp