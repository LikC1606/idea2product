# app/controllers/problem_controller.py

from flask import Blueprint, request, jsonify
from app.models import Problem, db
from sqlalchemy.exc import SQLAlchemyError

# Blueprint for the problem controller
problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    """
    Get all problems from the database.
    """
    try:
        problems = Problem.query.all()
        result = [problem.to_dict() for problem in problems]
        return jsonify({'success': True, 'data': result}), 200
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Get a single problem by its ID.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404
        return jsonify({'success': True, 'data': problem.to_dict()}), 200
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    """
    Create a new problem.
    """
    try:
        data = request.get_json()
        new_problem = Problem(
            title=data['title'],
            description=data['description'],
            difficulty=data['difficulty'],
            tags=data.get('tags', [])
        )
        db.session.add(new_problem)
        db.session.commit()
        return jsonify({'success': True, 'data': new_problem.to_dict()}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    except KeyError as e:
        return jsonify({'success': False, 'error': f'Missing field: {str(e)}'}), 400

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """
    Update an existing problem by its ID.
    """
    try:
        data = request.get_json()
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404
        
        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        problem.tags = data.get('tags', problem.tags)
        
        db.session.commit()
        return jsonify({'success': True, 'data': problem.to_dict()}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """
    Delete a problem by its ID.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'success': False, 'error': 'Problem not found'}), 404
        
        db.session.delete(problem)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Problem deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500