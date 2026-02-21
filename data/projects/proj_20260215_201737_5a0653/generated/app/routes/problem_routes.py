# app/routes/problem_routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.models import Problem, db

# Must Export
problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    """
    Fetch all problems from the database.
    """
    try:
        problems = Problem.query.all()
        result = [problem.to_dict() for problem in problems]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred', 'details': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Fetch a single problem by ID.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        return jsonify(problem.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred', 'details': str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def add_problem():
    """
    Add a new problem to the database.
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
        return jsonify(new_problem.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': 'Missing required field', 'details': str(e)}), 400
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred', 'details': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """
    Update an existing problem.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404

        data = request.get_json()
        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        problem.tags = data.get('tags', problem.tags)

        db.session.commit()
        return jsonify(problem.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred', 'details': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """
    Delete a problem from the database.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404

        db.session.delete(problem)
        db.session.commit()
        return jsonify({'message': 'Problem deleted successfully'}), 200
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred', 'details': str(e)}), 500