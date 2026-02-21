from flask import Blueprint, request, jsonify, render_template
from app.database import SessionLocal, User, Problem, Submission, Solution

routes_bp = Blueprint('routes', __name__)

# Home route
@routes_bp.route('/')
def home():
    return render_template('index.html')

# Route to get all problems
@routes_bp.route('/problems', methods=['GET'])
def get_all_problems():
    session = SessionLocal()
    try:
        problems = session.query(Problem).all()
        return jsonify([problem.as_dict() for problem in problems])
    finally:
        session.close()

# Route to get a single problem by ID
@routes_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem_by_id(problem_id):
    session = SessionLocal()
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            return jsonify(problem.as_dict())
        return jsonify({'error': 'Problem not found'}), 404
    finally:
        session.close()

# Route to create a new problem
@routes_bp.route('/problems', methods=['POST'])
def create_problem():
    data = request.json
    session = SessionLocal()
    try:
        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty')
        )
        session.add(new_problem)
        session.commit()
        return jsonify(new_problem.as_dict()), 201
    finally:
        session.close()

# Route to update a problem
@routes_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    data = request.json
    session = SessionLocal()
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            session.commit()
            return jsonify(problem.as_dict())
        return jsonify({'error': 'Problem not found'}), 404
    finally:
        session.close()

# Route to delete a problem
@routes_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    session = SessionLocal()
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            session.delete(problem)
            session.commit()
            return jsonify({'message': 'Problem deleted successfully'})
        return jsonify({'error': 'Problem not found'}), 404
    finally:
        session.close()

# Route to get all users
@routes_bp.route('/users', methods=['GET'])
def get_all_users():
    session = SessionLocal()
    try:
        users = session.query(User).all()
        return jsonify([user.as_dict() for user in users])
    finally:
        session.close()

# Route to get a single user by ID
@routes_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return jsonify(user.as_dict())
        return jsonify({'error': 'User not found'}), 404
    finally:
        session.close()

# Route to create a new user
@routes_bp.route('/users', methods=['POST'])
def create_user():
    data = request.json
    session = SessionLocal()
    try:
        new_user = User(
            username=data.get('username'),
            email=data.get('email')
        )
        session.add(new_user)
        session.commit()
        return jsonify(new_user.as_dict()), 201
    finally:
        session.close()

# Route to update a user
@routes_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.username = data.get('username', user.username)
            user.email = data.get('email', user.email)
            session.commit()
            return jsonify(user.as_dict())
        return jsonify({'error': 'User not found'}), 404
    finally:
        session.close()

# Route to delete a user
@routes_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
            return jsonify({'message': 'User deleted successfully'})
        return jsonify({'error': 'User not found'}), 404
    finally:
        session.close()