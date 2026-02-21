from flask import Blueprint, request, jsonify, render_template
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User
from app.database import db

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def list_solutions():
    try:
        solutions = Solution.get_all_solutions()
        return jsonify([solution.to_dict() for solution in solutions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    try:
        solution = Solution.get_by_id(solution_id)
        if solution:
            return jsonify(solution.to_dict()), 200
        else:
            return jsonify({'error': 'Solution not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_bp.route('/solutions/create', methods=['POST'])
def create_solution():
    try:
        data = request.json
        user_id = data.get('user_id')
        problem_id = data.get('problem_id')
        code = data.get('code')

        user = User.get_by_id(user_id)
        problem = Problem.get_by_id(problem_id)
        
        if not user or not problem:
            return jsonify({'error': 'Invalid user or problem'}), 400
        
        solution = Solution(user_id=user_id, problem_id=problem_id, code=code)
        db.session.add(solution)
        db.session.commit()
        return jsonify(solution.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_bp.route('/solutions/<int:solution_id>/edit', methods=['PUT'])
def edit_solution(solution_id):
    try:
        data = request.json
        solution = Solution.get_by_id(solution_id)
        
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        solution.code = data.get('code', solution.code)
        db.session.add(solution)
        db.session.commit()
        return jsonify(solution.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@solution_bp.route('/solutions/<int:solution_id>/delete', methods=['DELETE'])
def delete_solution(solution_id):
    try:
        solution = Solution.get_by_id(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        db.session.delete(solution)
        db.session.commit()
        return jsonify({'message': 'Solution deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500