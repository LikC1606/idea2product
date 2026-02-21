from flask import Blueprint, jsonify, request
from app.models.user import User
from app.database import db

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        try:
            users = User.query.all()
            user_list = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
            return jsonify({'success': True, 'data': user_list}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            user_data = {'id': user.id, 'username': user.username, 'email': user.email}
            return jsonify({'success': True, 'data': user_data}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            if not username or not email:
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            new_user = User(username=username, email=email)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User created successfully'}), 201
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            data = request.get_json()
            user.username = data.get('username', user.username)
            user.email = data.get('email', user.email)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User updated successfully'}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            db.session.delete(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    return user_bp