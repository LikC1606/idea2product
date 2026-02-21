from flask import Blueprint, request, jsonify
from app.models.solution import Solution

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/submit', methods=['POST'])
    def submit_solution():
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            problem_id = data.get('problem_id')
            code = data.get('code')

            if not user_id or not problem_id or not code:
                return jsonify({'error': 'Missing required fields'}), 400

            solution = Solution(user_id=user_id, problem_id=problem_id, code=code)
            solution.save()

            return jsonify({'message': 'Solution submitted successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions', methods=['GET'])
    def get_solutions():
        try:
            solutions = Solution.query.all()
            result = [solution.to_dict() for solution in solutions]
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solution/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404

            return jsonify(solution.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return blueprint