from flask import Blueprint, request, jsonify
from app.models.user import User
from app.database import db

def user_blueprint():
    blueprint = Blueprint('user', __name__)

    @blueprint.route('/user', methods=['GET'])
    def get_users():
        try:
            users = User.query.all()
            return jsonify([user.to_dict() for user in users]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/user', methods=['POST'])
    def create_user():
        try:
            data = request.json
            username = data.get('username')
            email = data.get('email')

            if not username or not email:
                return jsonify({'error': 'Missing username or email'}), 400

            new_user = User(username=username, email=email)
            db.session.add(new_user)
            db.session.commit()

            return jsonify(new_user.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/user/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404

            return jsonify(user.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/user/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        try:
            data = request.json
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
            return jsonify(user.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/user/<int:user_id>', methods=['DELETE'])
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

    return blueprint