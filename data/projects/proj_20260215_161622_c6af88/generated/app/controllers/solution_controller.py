from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.database import db

solution_controller = Blueprint('solution_controller', __name__)

@solution_controller.route('/solutions', methods=['GET'])
def get_solutions():
    try:
        solutions = Solution.query.all()
        solutions_list = [solution.to_dict() for solution in solutions]
        return jsonify({'solutions': solutions_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_controller.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    try:
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        return jsonify(solution.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_controller.route('/solutions', methods=['POST'])
def create_solution():
    try:
        data = request.get_json()
        new_solution = Solution(
            problem_id=data.get('problem_id'),
            user_id=data.get('user_id'),
            code=data.get('code'),
            language=data.get('language'),
            result=data.get('result')
        )
        db.session.add(new_solution)
        db.session.commit()
        return jsonify(new_solution.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@solution_controller.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    try:
        data = request.get_json()
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        
        solution.problem_id = data.get('problem_id', solution.problem_id)
        solution.user_id = data.get('user_id', solution.user_id)
        solution.code = data.get('code', solution.code)
        solution.language = data.get('language', solution.language)
        solution.result = data.get('result', solution.result)
        
        db.session.commit()
        return jsonify(solution.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@solution_controller.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    try:
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        db.session.delete(solution)
        db.session.commit()
        return jsonify({'message': 'Solution deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500