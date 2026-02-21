from flask import Blueprint
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        # Normally, we would interact here with User model or database
        return {"message": "List of users"}

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        # Placeholder for fetching a specific user
        return {"message": f"Details of user {user_id}"}

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        # Placeholder for creating a new user
        return {"message": "User created successfully"}, 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        # Placeholder for updating user details
        return {"message": f"User {user_id} updated successfully"}

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        # Placeholder for deleting a user
        return {"message": f"User {user_id} deleted successfully"}

    return user_bp