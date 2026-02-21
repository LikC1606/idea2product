from flask import Blueprint, request, jsonify
from app.database import db
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

# Endpoint to list all solutions
@solution_bp.route('/solutions/', methods=['GET'])
def list_solutions():
    solutions = Solution.query.all()
    return jsonify([solution.to_dict() for solution in solutions]), 200

# Endpoint to view a specific solution
@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404
    return jsonify(solution.to_dict()), 200

# Endpoint to create a new solution
@solution_bp.route('/solutions/create', methods=['POST'])
def create_solution():
    data = request.get_json()
    if not data or 'problem_id' not in data or 'user_id' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    problem = Problem.query.get(data['problem_id'])
    user = User.query.get(data['user_id'])
    if not problem or not user:
        return jsonify({'error': 'Problem or User not found'}), 404

    new_solution = Solution(
        problem_id=data['problem_id'],
        user_id=data['user_id'],
        content=data['content']
    )
    db.session.add(new_solution)
    db.session.commit()

    return jsonify(new_solution.to_dict()), 201

# Endpoint to edit an existing solution
@solution_bp.route('/solutions/<int:solution_id>/edit', methods=['PUT'])
def edit_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    solution.content = data.get('content', solution.content)
    db.session.commit()

    return jsonify(solution.to_dict()), 200

# Endpoint to delete a solution
@solution_bp.route('/solutions/<int:solution_id>/delete', methods=['DELETE'])
def delete_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    db.session.delete(solution)
    db.session.commit()

    return jsonify({'message': 'Solution deleted successfully'}), 200