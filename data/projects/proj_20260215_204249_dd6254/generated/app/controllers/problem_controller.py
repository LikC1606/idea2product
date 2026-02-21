from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    """
    Get a list of all problems.
    """
    session = SessionLocal()
    try:
        problems = session.query(Problem).all()
        result = [problem.to_dict() for problem in problems]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': 'Failed to fetch problems', 'details': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Get a specific problem by its ID.
    """
    session = SessionLocal()
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            return jsonify(problem.to_dict()), 200
        else:
            return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': 'Failed to fetch problem', 'details': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    """
    Create a new problem.
    """
    session = SessionLocal()
    data = request.json
    try:
        new_problem = Problem(
            title=data['title'],
            description=data['description'],
            difficulty=data['difficulty']
        )
        session.add(new_problem)
        session.commit()
        return jsonify(new_problem.to_dict()), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': 'Failed to create problem', 'details': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """
    Update an existing problem.
    """
    session = SessionLocal()
    data = request.json
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            session.commit()
            return jsonify(problem.to_dict()), 200
        else:
            return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': 'Failed to update problem', 'details': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """
    Delete a problem by its ID.
    """
    session = SessionLocal()
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            session.delete(problem)
            session.commit()
            return jsonify({'message': 'Problem deleted successfully'}), 200
        else:
            return jsonify({'error': 'Problem not found'}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': 'Failed to delete problem', 'details': str(e)}), 500
    finally:
        session.close()