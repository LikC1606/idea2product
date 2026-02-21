from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal, User

user_bp = Blueprint('user', __name__)

# Helper function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Route to get all users
@user_bp.route('/users', methods=['GET'])
def get_users():
    db = next(get_db())
    try:
        users = db.query(User).all()
        return jsonify([user.to_dict() for user in users]), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

# Route to get a specific user by ID
@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

# Route to create a new user
@user_bp.route('/users', methods=['POST'])
def create_user():
    db = next(get_db())
    try:
        data = request.get_json()
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password')  # Assuming password is hashed before storing
        )
        db.add(new_user)
        db.commit()
        return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Route to update an existing user
@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    db = next(get_db())
    try:
        data = request.get_json()
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'password' in data:
                user.password = data['password']  # Assuming password is hashed before storing
            db.commit()
            return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Route to delete a user
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500