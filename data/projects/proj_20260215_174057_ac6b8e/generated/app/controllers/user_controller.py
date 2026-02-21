from flask import Blueprint
from app.models.user import User

def user_blueprint():
    user_bp = Blueprint('user', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        # Example logic to retrieve all users
        users = User.query.all()
        return {"users": [user.to_dict() for user in users]}, 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        # Example logic to retrieve a specific user by ID
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}, 404
        return user.to_dict(), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        # Example logic to create a new user
        data = request.json
        new_user = User(**data)
        db.session.add(new_user)
        db.session.commit()
        return new_user.to_dict(), 201

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        # Example logic to delete a user
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}, 404
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}, 200

    return user_bp