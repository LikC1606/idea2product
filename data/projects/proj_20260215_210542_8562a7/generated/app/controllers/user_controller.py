from flask import Blueprint, request, jsonify, render_template
from app.database import db
from app.models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/users/', methods=['GET'])
def list_users():
    """Fetch all users."""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def view_user(user_id):
    """Fetch a specific user by ID."""
    try:
        user = User.query.get(user_id)
        if user:
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users/create', methods=['POST'])
def create_user():
    """Create a new user."""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')

        if not username or not email:
            return jsonify({"error": "Missing required fields"}), 400

        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()

        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users/<int:user_id>/edit', methods=['PUT'])
def edit_user(user_id):
    """Edit an existing user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        username = data.get('username')
        email = data.get('email')

        if username:
            user.username = username
        if email:
            user.email = email

        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500