from flask import Blueprint, request, jsonify, render_template
from app.database import db
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def list_solutions():
    """
    List all solutions.
    """
    solutions = Solution.query.all()
    return jsonify([solution.to_dict() for solution in solutions]), 200

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    """
    View a specific solution by ID.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404
    return jsonify(solution.to_dict()), 200

@solution_bp.route('/solutions/new', methods=['POST'])
def create_solution():
    """
    Create a new solution.
    """
    data = request.get_json()
    problem_id = data.get('problem_id')
    user_id = data.get('user_id')
    content = data.get('content')

    # Validate problem and user existence
    problem = Problem.query.get(problem_id)
    if not problem:
        return jsonify({'error': 'Problem not found'}), 404

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Create new solution
    solution = Solution(problem_id=problem_id, user_id=user_id, content=content)
    db.session.add(solution)
    db.session.commit()

    return jsonify(solution.to_dict()), 201

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """
    Update an existing solution.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    data = request.get_json()
    solution.content = data.get('content', solution.content)

    db.session.commit()
    return jsonify(solution.to_dict()), 200

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """
    Delete a solution by ID.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    db.session.delete(solution)
    db.session.commit()
    return jsonify({'message': 'Solution deleted successfully'}), 200