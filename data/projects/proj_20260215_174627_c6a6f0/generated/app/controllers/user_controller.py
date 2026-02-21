from flask import Blueprint
from app.models.user import User

def user_blueprint():
    blueprint = Blueprint('user', __name__)

    @blueprint.route('/users', methods=['GET'])
    def get_users():
        # Mock function to simulate fetching users
        users = User.query.all()  # Assuming User has a query property
        return {'users': [user.to_dict() for user in users]}, 200

    @blueprint.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        # Mock function to simulate fetching a single user by ID
        user = User.query.get(user_id)
        if user:
            return user.to_dict(), 200
        return {'error': 'User not found'}, 404

    @blueprint.route('/users', methods=['POST'])
    def create_user():
        # Mock function to simulate user creation
        return {'message': 'User creation endpoint'}, 201

    @blueprint.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        # Mock function to simulate user update
        return {'message': f'User {user_id} update endpoint'}, 200

    @blueprint.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        # Mock function to simulate user deletion
        return {'message': f'User {user_id} deletion endpoint'}, 200

    return blueprint