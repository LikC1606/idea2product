from flask import Blueprint, request, jsonify
from app.models.user import User
from app.database import db_session

user_profile_bp = Blueprint('user_profile', __name__)

@user_profile_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Retrieve user profile information."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'solved_problems': user.solved_problems,
        'rank': user.rank
    }
    return jsonify(user_data), 200

@user_profile_bp.route('/profile/<int:user_id>', methods=['PUT'])
def update_user_profile(user_id):
    """Update user profile information."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    try:
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.set_password(data['password'])  # Assuming `set_password` hashes the password
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 400
    
    return jsonify({'message': 'Profile updated successfully'}), 200

@user_profile_bp.route('/profile/<int:user_id>', methods=['DELETE'])
def delete_user_profile(user_id):
    """Delete a user profile."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        db_session.delete(user)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 400
    
    return jsonify({'message': 'Profile deleted successfully'}), 200