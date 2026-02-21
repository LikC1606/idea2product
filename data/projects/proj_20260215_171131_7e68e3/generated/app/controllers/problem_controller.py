from flask import Blueprint, jsonify, request
from app.models.problem import Problem

def problem_blueprint():
    problems_bp = Blueprint('problems', __name__)

    @problems_bp.route('/problems', methods=['GET'])
    def get_problems():
        # Simulate retrieving all problems (no database operations defined)
        problems = Problem.get_all_problems()  # Assuming a method exists in Problem model
        return jsonify([problem.to_dict() for problem in problems]), 200

    @problems_bp.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Simulate retrieving a single problem by ID
        problem = Problem.get_problem_by_id(problem_id)  # Assuming a method exists in Problem model
        if problem:
            return jsonify(problem.to_dict()), 200
        return jsonify({"error": "Problem not found"}), 404

    @problems_bp.route('/problems', methods=['POST'])
    def create_problem():
        data = request.get_json()
        try:
            problem = Problem.create_problem(data)  # Assuming a method exists in Problem model
            return jsonify(problem.to_dict()), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @problems_bp.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        data = request.get_json()
        try:
            updated_problem = Problem.update_problem(problem_id, data)  # Assuming a method exists in Problem model
            if updated_problem:
                return jsonify(updated_problem.to_dict()), 200
            return jsonify({"error": "Problem not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @problems_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        try:
            success = Problem.delete_problem(problem_id)  # Assuming a method exists in Problem model
            if success:
                return jsonify({"message": "Problem deleted successfully"}), 200
            return jsonify({"error": "Problem not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return problems_bp