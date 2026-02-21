from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.database import db

solution_controller = Blueprint('solution_controller', __name__)

@solution_controller.route('/solutions', methods=['GET'])
def get_solutions():
    try:
        solutions = Solution.query.all()
        return jsonify([solution.to_dict() for solution in solutions]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@solution_controller.route('/solutions/<int:id>', methods=['GET'])
def get_solution_by_id(id):
    try:
        solution = Solution.query.get(id)
        if solution:
            return jsonify(solution.to_dict()), 200
        else:
            return jsonify({"error": "Solution not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@solution_controller.route('/solutions', methods=['POST'])
def create_solution():
    try:
        data = request.json
        new_solution = Solution(**data)
        db.session.add(new_solution)
        db.session.commit()
        return jsonify(new_solution.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@solution_controller.route('/solutions/<int:id>', methods=['PUT'])
def update_solution(id):
    try:
        solution = Solution.query.get(id)
        if solution:
            data = request.json
            for key, value in data.items():
                if hasattr(solution, key):
                    setattr(solution, key, value)
            db.session.commit()
            return jsonify(solution.to_dict()), 200
        else:
            return jsonify({"error": "Solution not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@solution_controller.route('/solutions/<int:id>', methods=['DELETE'])
def delete_solution(id):
    try:
        solution = Solution.query.get(id)
        if solution:
            db.session.delete(solution)
            db.session.commit()
            return jsonify({"message": "Solution deleted successfully"}), 200
        else:
            return jsonify({"error": "Solution not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500