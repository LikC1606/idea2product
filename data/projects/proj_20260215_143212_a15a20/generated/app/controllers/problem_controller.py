from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models.problem import Problem
from app.database import db_session

problem_controller = Blueprint('problem_controller', __name__)

@problem_controller.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = db_session.query(Problem).all()
        return jsonify([problem.to_dict() for problem in problems]), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@problem_controller.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    try:
        problem = db_session.query(Problem).filter_by(id=problem_id).first()
        if problem:
            return jsonify(problem.to_dict()), 200
        else:
            return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@problem_controller.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.json
        new_problem = Problem(title=data['title'],
                              description=data['description'],
                              difficulty=data['difficulty'])
        db_session.add(new_problem)
        db_session.commit()
        return jsonify(new_problem.to_dict()), 201
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@problem_controller.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        data = request.json
        problem = db_session.query(Problem).filter_by(id=problem_id).first()
        if problem:
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            db_session.commit()
            return jsonify(problem.to_dict()), 200
        else:
            return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@problem_controller.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = db_session.query(Problem).filter_by(id=problem_id).first()
        if problem:
            db_session.delete(problem)
            db_session.commit()
            return jsonify({'message': 'Problem deleted successfully'}), 200
        else:
            return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500