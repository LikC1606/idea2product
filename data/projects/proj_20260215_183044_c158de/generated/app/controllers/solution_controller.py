from flask import Blueprint, jsonify, request
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
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    return jsonify(solution.to_dict())

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    data = request.get_json()
    try:
        new_solution = Solution(**data)
        db.session.add(new_solution)
        db.session.commit()
        return jsonify(new_solution.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    data = request.get_json()
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    try:
        for key, value in data.items():
            setattr(solution, key, value)
        db.session.commit()
        return jsonify(solution.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    try:
        db.session.delete(solution)
        db.session.commit()
        return jsonify({"message": "Solution deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400