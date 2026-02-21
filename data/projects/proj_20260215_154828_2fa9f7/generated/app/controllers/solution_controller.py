from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.database import db

solution_controller = Blueprint('solution', __name__, url_prefix='/solutions')

@solution_controller.route('/submit', methods=['POST'])
def submit_solution():
    try:
        data = request.json
        if not data or 'problem_id' not in data or 'user_id' not in data or 'code' not in data:
            return jsonify({'error': 'Invalid submission data'}), 400

        solution = Solution(
            problem_id=data['problem_id'],
            user_id=data['user_id'],
            code=data['code']
        )
        db.session.add(solution)
        db.session.commit()

        return jsonify({'message': 'Solution submitted successfully', 'solution_id': solution.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@solution_controller.route('/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    try:
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        return jsonify({
            'solution_id': solution.id,
            'problem_id': solution.problem_id,
            'user_id': solution.user_id,
            'code': solution.code
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_controller.route('/all', methods=['GET'])
def get_all_solutions():
    try:
        solutions = Solution.query.all()
        solutions_data = [{
            'solution_id': solution.id,
            'problem_id': solution.problem_id,
            'user_id': solution.user_id,
            'code': solution.code
        } for solution in solutions]

        return jsonify(solutions_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500