from flask import Blueprint
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        # This is a placeholder for fetching and returning user data
        # Replace with actual business logic if needed
        return {"message": "List of users"}

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        # This is a placeholder for fetching a specific user's data
        # Replace with actual business logic if needed
        return {"message": f"User with ID {user_id}"}

    return user_bp