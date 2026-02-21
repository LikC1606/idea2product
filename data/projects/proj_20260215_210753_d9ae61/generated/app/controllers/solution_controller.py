from flask import Blueprint, request, jsonify, render_template
from app.database import db
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def list_solutions():
    """Handles GET requests to '/solutions'."""
    solutions = Solution.query.all()
    solution_list = [solution.to_dict() for solution in solutions]
    return jsonify(solution_list), 200

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    """Handles GET requests to '/solutions/<int:solution_id>'."""
    solution = Solution.query.get(solution_id)
    if solution:
        return jsonify(solution.to_dict()), 200
    return jsonify({'error': 'Solution not found'}), 404

@solution_bp.route('/solutions/new', methods=['POST'])
def create_solution():
    """Handles POST requests to '/solutions/new'."""
    data = request.json
    user_id = data.get('user_id')
    problem_id = data.get('problem_id')
    content = data.get('content')

    user = User.query.get(user_id)
    problem = Problem.query.get(problem_id)

    if not user or not problem:
        return jsonify({'error': 'Invalid user or problem'}), 400

    new_solution = Solution(user_id=user_id, problem_id=problem_id, content=content)
    db.session.add(new_solution)
    db.session.commit()
    
    return jsonify(new_solution.to_dict()), 201

@solution_bp.route('/solutions/<int:solution_id>/edit', methods=['PUT'])
def edit_solution(solution_id):
    """Handles PUT requests to '/solutions/<int:solution_id>/edit'."""
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    data = request.json
    content = data.get('content', solution.content)
    solution.content = content
    
    db.session.commit()
    return jsonify(solution.to_dict()), 200

@solution_bp.route('/solutions/<int:solution_id>/delete', methods=['DELETE'])
def delete_solution(solution_id):
    """Handles DELETE requests to '/solutions/<int:solution_id>/delete'."""
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    db.session.delete(solution)
    db.session.commit()
    return jsonify({'message': 'Solution deleted successfully'}), 200