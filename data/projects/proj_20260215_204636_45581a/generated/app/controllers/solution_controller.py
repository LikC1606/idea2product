from flask import Blueprint, request, jsonify
from app.database import db
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def get_solutions():
    """
    Retrieve all solutions from the database.
    """
    solutions = Solution.query.all()
    return jsonify([solution.to_dict() for solution in solutions]), 200

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    """
    Retrieve a specific solution by its ID.
    """
    solution = Solution.query.get(solution_id)
    if solution:
        return jsonify(solution.to_dict()), 200
    return jsonify({'error': 'Solution not found'}), 404

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    """
    Create a new solution.
    Request JSON should contain: user_id, problem_id, code, status.
    """
    data = request.get_json()

    # Validate necessary fields
    required_fields = ['user_id', 'problem_id', 'code', 'status']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate user and problem existence
    user = User.query.get(data['user_id'])
    problem = Problem.query.get(data['problem_id'])
    if not user or not problem:
        return jsonify({'error': 'Invalid user_id or problem_id'}), 400

    # Create and save the solution
    new_solution = Solution(
        user_id=data['user_id'],
        problem_id=data['problem_id'],
        code=data['code'],
        status=data['status']
    )
    db.session.add(new_solution)
    db.session.commit()

    return jsonify(new_solution.to_dict()), 201

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """
    Update an existing solution.
    Request JSON can contain: code, status.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    data = request.get_json()
    if 'code' in data:
        solution.code = data['code']
    if 'status' in data:
        solution.status = data['status']

    db.session.commit()
    return jsonify(solution.to_dict()), 200

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """
    Delete a solution by its ID.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    db.session.delete(solution)
    db.session.commit()
    return jsonify({'message': 'Solution deleted successfully'}), 200