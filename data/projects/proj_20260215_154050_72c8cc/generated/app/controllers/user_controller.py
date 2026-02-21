from flask import Blueprint, request, jsonify
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint("user", __name__)

    @user_bp.route("/users", methods=["GET"])
    def get_users():
        # Simulated response since database operations are not required.
        users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
        return jsonify(users), 200

    @user_bp.route("/users/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        # Simulated response since database operations are not required.
        user = {"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}
        return jsonify(user), 200

    @user_bp.route("/users", methods=["POST"])
    def create_user():
        data = request.get_json()
        # Simulated response since database operations are not required.
        new_user = {
            "id": 3,  # Example ID for the newly created user
            "name": data.get("name"),
            "email": data.get("email"),
        }
        return jsonify(new_user), 201

    @user_bp.route("/users/<int:user_id>", methods=["PUT"])
    def update_user(user_id):
        data = request.get_json()
        # Simulated response since database operations are not required.
        updated_user = {
            "id": user_id,
            "name": data.get("name", f"User{user_id}"),
            "email": data.get("email", f"user{user_id}@example.com"),
        }
        return jsonify(updated_user), 200

    @user_bp.route("/users/<int:user_id>", methods=["DELETE"])
    def delete_user(user_id):
        # Simulated response since database operations are not required.
        return jsonify({"message": f"User {user_id} deleted successfully"}), 200

    return user_bp