from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.database import db

solution_controller = Blueprint('solution', __name__)

@solution_controller.route('/solutions', methods=['GET'])
def get_solutions():
    try:
        solutions = Solution.query.all()
        result = [solution.to_dict() for solution in solutions]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@solution_controller.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    try:
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({"error": "Solution not found"}), 404
        return jsonify(solution.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@solution_controller.route('/solutions', methods=['POST'])
def create_solution():
    try:
        data = request.get_json()
        new_solution = Solution(**data)
        db.session.add(new_solution)
        db.session.commit()
        return jsonify(new_solution.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@solution_controller.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    try:
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({"error": "Solution not found"}), 404
        data = request.get_json()
        for key, value in data.items():
            setattr(solution, key, value)
        db.session.commit()
        return jsonify(solution.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@solution_controller.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    try:
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({"error": "Solution not found"}), 404
        db.session.delete(solution)
        db.session.commit()
        return jsonify({"message": "Solution deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500