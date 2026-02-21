from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.database import db

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/solutions', methods=['POST'])
    def submit_solution():
        try:
            data = request.get_json()
            code = data.get('code')
            problem_id = data.get('problem_id')
            user_id = data.get('user_id')

            if not code or not problem_id or not user_id:
                return jsonify({"error": "Missing required fields"}), 400

            solution = Solution(code=code, problem_id=problem_id, user_id=user_id)
            db.session.add(solution)
            db.session.commit()

            return jsonify({"message": "Solution submitted successfully", "solution_id": solution.id}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @blueprint.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({"error": "Solution not found"}), 404

            return jsonify({
                "id": solution.id,
                "code": solution.code,
                "problem_id": solution.problem_id,
                "user_id": solution.user_id,
                "created_at": solution.created_at
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return blueprint