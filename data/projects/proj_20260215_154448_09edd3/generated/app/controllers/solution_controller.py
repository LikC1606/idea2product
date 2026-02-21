from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.database import db

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/submit_solution', methods=['POST'])
    def submit_solution():
        try:
            data = request.get_json()
            if not data or 'problem_id' not in data or 'user_id' not in data or 'code' not in data:
                return jsonify({'error': 'Invalid input'}), 400

            solution = Solution(
                problem_id=data['problem_id'],
                user_id=data['user_id'],
                code=data['code'],
                status="submitted"
            )
            db.session.add(solution)
            db.session.commit()

            return jsonify({'message': 'Solution submitted successfully', 'solution_id': solution.id}), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/get_solution/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404

            solution_data = {
                'id': solution.id,
                'problem_id': solution.problem_id,
                'user_id': solution.user_id,
                'code': solution.code,
                'status': solution.status,
                'created_at': solution.created_at,
                'updated_at': solution.updated_at
            }
            return jsonify(solution_data), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return blueprint