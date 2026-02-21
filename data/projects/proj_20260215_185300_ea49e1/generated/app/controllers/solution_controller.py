from flask import Blueprint, jsonify
from app.models.solution import Solution
from app.database import db

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def get_solutions():
    solutions = Solution.query.all()
    return jsonify([solution.to_dict() for solution in solutions])

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if solution is None:
        return jsonify({'error': 'Solution not found'}), 404
    return jsonify(solution.to_dict())

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    # Assuming request.json contains the required data
    data = request.get_json()
    solution = Solution(**data)
    db.session.add(solution)
    db.session.commit()
    return jsonify(solution.to_dict()), 201

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if solution is None:
        return jsonify({'error': 'Solution not found'}), 404
    data = request.get_json()
    for key, value in data.items():
        setattr(solution, key, value)
    db.session.commit()
    return jsonify(solution.to_dict())

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if solution is None:
        return jsonify({'error': 'Solution not found'}), 404
    db.session.delete(solution)
    db.session.commit()
    return jsonify({'message': 'Solution deleted successfully'})