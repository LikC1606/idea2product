from flask import Blueprint, jsonify
from app.models.solution import Solution
from app.database import db

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def get_solutions():
    try:
        solutions = Solution.query.all()
        solution_list = [solution.to_dict() for solution in solutions]
        return jsonify(solution_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    try:
        solution = Solution.query.get(solution_id)
        if solution:
            return jsonify(solution.to_dict()), 200
        else:
            return jsonify({'message': 'Solution not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500