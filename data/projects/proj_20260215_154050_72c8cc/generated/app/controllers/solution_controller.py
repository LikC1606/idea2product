from flask import Blueprint, request, jsonify
from app.models.solution import Solution

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/submit-solution', methods=['POST'])
    def submit_solution():
        try:
            data = request.get_json()
            if not data or not all(k in data for k in ('problem_id', 'user_id', 'code', 'language')):
                return jsonify({'error': 'Missing required fields'}), 400

            # Create a new solution instance
            solution = Solution(
                problem_id=data['problem_id'],
                user_id=data['user_id'],
                code=data['code'],
                language=data['language']
            )
            
            # Simulate saving to database (replace with actual db logic if needed)
            # db.session.add(solution)
            # db.session.commit()

            return jsonify({'message': 'Solution submitted successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solution/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            # Simulate fetching from database (replace with actual db logic if needed)
            # solution = Solution.query.get(solution_id)
            solution = None  # Placeholder for database query

            if not solution:
                return jsonify({'error': 'Solution not found'}), 404

            # Serialize the solution (dummy data used here for illustration)
            solution_data = {
                'id': solution_id,
                'problem_id': solution.problem_id,
                'user_id': solution.user_id,
                'code': solution.code,
                'language': solution.language
            }
            return jsonify(solution_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return blueprint