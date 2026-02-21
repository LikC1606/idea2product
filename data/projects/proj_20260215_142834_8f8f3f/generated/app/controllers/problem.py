from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models.problem import Problem, db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = Problem.query.all()
        return jsonify([problem.to_dict() for problem in problems]), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem:
            return jsonify(problem.to_dict()), 200
        return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    data = request.json
    try:
        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty')
        )
        db.session.add(new_problem)
        db.session.commit()
        return jsonify(new_problem.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    data = request.json
    try:
        problem = Problem.query.get(problem_id)
        if problem:
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            db.session.commit()
            return jsonify(problem.to_dict()), 200
        return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem:
            db.session.delete(problem)
            db.session.commit()
            return jsonify({'message': 'Problem deleted successfully'}), 200
        return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500