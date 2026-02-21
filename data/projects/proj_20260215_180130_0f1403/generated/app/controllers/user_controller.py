from flask import Blueprint
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def list_users():
        # Logic to list all users (dummy data since no database is used)
        users = [
            {"id": 1, "username": "user1", "email": "user1@example.com"},
            {"id": 2, "username": "user2", "email": "user2@example.com"}
        ]
        return {"users": users}, 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        # Logic to get a specific user by ID (dummy data since no database is used)
        user = {"id": user_id, "username": f"user{user_id}", "email": f"user{user_id}@example.com"}
        return {"user": user}, 200

    return user_bp