from flask import Blueprint, request, jsonify

def user_bp():
    user_blueprint = Blueprint('user', __name__)
    
    @user_blueprint.route('/users', methods=['GET'])
    def get_users():
        # Logic for retrieving users would go here
        return jsonify({"message": "Retrieve all users"}), 200

    @user_blueprint.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        # Logic for retrieving a specific user would go here
        return jsonify({"message": f"Retrieve user with ID {user_id}"}), 200

    @user_blueprint.route('/users', methods=['POST'])
    def create_user():
        # Logic for creating a new user would go here
        user_data = request.json
        return jsonify({"message": "User created successfully", "data": user_data}), 201

    @user_blueprint.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        # Logic for updating a user would go here
        update_data = request.json
        return jsonify({"message": f"User with ID {user_id} updated successfully", "data": update_data}), 200

    @user_blueprint.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        # Logic for deleting a user would go here
        return jsonify({"message": f"User with ID {user_id} deleted successfully"}), 200

    return user_blueprint