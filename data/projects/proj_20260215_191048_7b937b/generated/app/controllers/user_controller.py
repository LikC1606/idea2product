from flask import Blueprint, jsonify
from app.models.user import User
from app.database import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    users_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
    return jsonify(users_list)

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email})

@user_bp.route('/users', methods=['POST'])
def create_user():
    # Example implementation - adjust based on actual data structure
    # Assuming request.json contains {'name': '...', 'email': '...'}
    from flask import request
    data = request.json
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Invalid input'}), 400
    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created', 'id': new_user.id}), 201

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    from flask import request
    data = request.json
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    if not data:
        return jsonify({'error': 'Invalid input'}), 400
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify({'message': 'User updated'})

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})