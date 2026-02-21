from flask import Blueprint, jsonify, request
from app.controllers.user_controller import (
    get_users,
    get_user,
    create_user,
    update_user,
    delete_user
)

user_routes_bp = Blueprint('user_routes', __name__)

@user_routes_bp.route('/users', methods=['GET'])
def list_users():
    """Endpoint to list all users."""
    users = get_users()
    return jsonify(users), 200

@user_routes_bp.route('/users/<int:user_id>', methods=['GET'])
def retrieve_user(user_id):
    """Endpoint to retrieve a specific user by ID."""
    user = get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user), 200

@user_routes_bp.route('/users', methods=['POST'])
def add_user():
    """Endpoint to create a new user."""
    user_data = request.get_json()
    if not user_data:
        return jsonify({'error': 'Invalid input'}), 400
    new_user = create_user(user_data)
    return jsonify(new_user), 201

@user_routes_bp.route('/users/<int:user_id>', methods=['PUT'])
def modify_user(user_id):
    """Endpoint to update user information."""
    user_data = request.get_json()
    if not user_data:
        return jsonify({'error': 'Invalid input'}), 400
    updated_user = update_user(user_id, user_data)
    if not updated_user:
        return jsonify({'error': 'User not found or update failed'}), 404
    return jsonify(updated_user), 200

@user_routes_bp.route('/users/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
    """Endpoint to delete a user."""
    deleted = delete_user(user_id)
    if not deleted:
        return jsonify({'error': 'User not found or delete failed'}), 404
    return jsonify({'message': 'User deleted successfully'}), 200