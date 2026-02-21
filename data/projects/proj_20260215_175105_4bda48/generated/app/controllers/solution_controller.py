from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app import db  # Ensure db is imported

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/solutions', methods=['POST'])
    def create_solution():
        try:
            data = request.get_json()
            if not data or 'code' not in data or 'problem_id' not in data or 'user_id' not in data:
                return jsonify({'error': 'Invalid input'}), 400
            
            # Create a new solution instance
            new_solution = Solution(
                code=data['code'],
                problem_id=data['problem_id'],
                user_id=data['user_id']
            )

            # Save the solution to the database
            db.session.add(new_solution)
            db.session.commit()
            return jsonify({'message': 'Solution created successfully', 'solution': new_solution.to_dict()}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404
            
            return jsonify({'solution': solution.to_dict()}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions', methods=['GET'])
    def get_all_solutions():
        try:
            solutions = Solution.query.all()
            return jsonify({'solutions': [solution.to_dict() for solution in solutions]}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return blueprint