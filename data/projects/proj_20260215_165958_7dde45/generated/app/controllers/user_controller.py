from flask import Blueprint, jsonify, request
from app.models.user import User
from app.database import db

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        users = User.query.all()
        user_list = [user.to_dict() for user in users]
        return jsonify(user_list), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        data = request.json
        if not data or not data.get('name') or not data.get('email'):
            return jsonify({'error': 'Invalid input'}), 400
        
        new_user = User(name=data['name'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        db.session.commit()
        return jsonify(user.to_dict()), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200

    return user_bp