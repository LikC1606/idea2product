from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.database import db
from app.models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def list_users():
    """Retrieve a list of all users."""
    try:
        users = User.query.all()
        user_list = [{"id": user.id, "username": user.username, "email": user.email} for user in users]
        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/user/<int:user_id>', methods=['GET'])
def view_user(user_id):
    """Retrieve details of a specific user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        user_data = {"id": user.id, "username": user.username, "email": user.email}
        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/user/new', methods=['POST'])
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
        return jsonify({"message": "User created successfully", "user_id": new_user.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/user/<int:user_id>/edit', methods=['PUT'])
def edit_user(user_id):
    """Edit an existing user's information."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        data = request.json
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        db.session.commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/user/<int:user_id>/delete', methods=['DELETE'])
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