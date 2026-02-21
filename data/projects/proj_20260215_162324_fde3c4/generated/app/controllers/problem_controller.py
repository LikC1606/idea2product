from flask import Blueprint, request, jsonify
from app.models.problem import Problem
from app.database import db

problem_controller_bp = Blueprint('problem_controller', __name__)

@problem_controller_bp.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = Problem.query.all()
        problems_data = [problem.to_dict() for problem in problems]
        return jsonify({'success': True, 'problems': problems_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_controller_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404
        return jsonify({'success': True, 'problem': problem.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_controller_bp.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty')
        )
        db.session.add(new_problem)
        db.session.commit()
        return jsonify({'success': True, 'problem': new_problem.to_dict()}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_controller_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        
        db.session.commit()
        return jsonify({'success': True, 'problem': problem.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_controller_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404
        
        db.session.delete(problem)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Problem deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def problem_controller():
    return problem_controller_bp