from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.database import db

def solution_blueprint():
    solution_bp = Blueprint('solution', __name__)

    @solution_bp.route('/submit', methods=['POST'])
    def submit_solution():
        try:
            data = request.get_json()
            if not data or 'problem_id' not in data or 'user_id' not in data or 'code' not in data:
                return jsonify({'error': 'Invalid submission data'}), 400
            
            new_solution = Solution(
                problem_id=data['problem_id'],
                user_id=data['user_id'],
                code=data['code'],
                status='Pending'
            )
            db.session.add(new_solution)
            db.session.commit()
            return jsonify({'message': 'Solution submitted successfully', 'solution_id': new_solution.id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'An error occurred during submission', 'details': str(e)}), 500

    @solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404
            
            return jsonify({
                'solution_id': solution.id,
                'problem_id': solution.problem_id,
                'user_id': solution.user_id,
                'code': solution.code,
                'status': solution.status,
                'submitted_at': solution.submitted_at
            }), 200
        except Exception as e:
            return jsonify({'error': 'An error occurred while fetching solution', 'details': str(e)}), 500

    return solution_bp