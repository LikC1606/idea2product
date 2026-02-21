from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db_session

problem_library_bp = Blueprint('problem_library', __name__)

@problem_library_bp.route('/problems', methods=['GET'])
def get_all_problems():
    try:
        problems = Problem.query.all()
        problem_list = [problem.to_dict() for problem in problems]
        return jsonify({'success': True, 'data': problem_list}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_library_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404
        return jsonify({'success': True, 'data': problem.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_library_bp.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.json
        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty'),
            tags=data.get('tags'),
            sample_input=data.get('sample_input'),
            sample_output=data.get('sample_output')
        )
        db_session.add(new_problem)
        db_session.commit()
        return jsonify({'success': True, 'data': new_problem.to_dict()}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_library_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404

        data = request.json
        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        problem.tags = data.get('tags', problem.tags)
        problem.sample_input = data.get('sample_input', problem.sample_input)
        problem.sample_output = data.get('sample_output', problem.sample_output)

        db_session.commit()
        return jsonify({'success': True, 'data': problem.to_dict()}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_library_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404

        db_session.delete(problem)
        db_session.commit()
        return jsonify({'success': True, 'message': 'Problem deleted successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500