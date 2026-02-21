from flask import Blueprint, request, jsonify
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        # Simulating fetching users (as the database is not included in specifications)
        users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ]
        return jsonify(users), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        # Simulating fetching a single user
        user = {"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}
        return jsonify(user), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({"error": "Invalid input"}), 400

        # Simulate user creation
        new_user = {
            "id": 3,  # Example fixed ID
            "name": data['name'],
            "email": data['email']
        }
        return jsonify(new_user), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        data = request.get_json()
        if not data or ('name' not in data and 'email' not in data):
            return jsonify({"error": "Invalid input"}), 400

        # Simulate user update
        updated_user = {
            "id": user_id,
            "name": data.get('name', f"User{user_id}"),
            "email": data.get('email', f"user{user_id}@example.com")
        }
        return jsonify(updated_user), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        # Simulate user deletion
        return jsonify({"message": f"User {user_id} deleted"}), 200

    return user_bp