from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    """
    Retrieve a list of all problems.
    """
    session = SessionLocal()
    try:
        problems = session.query(Problem).all()
        result = [problem.to_dict() for problem in problems]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Retrieve a single problem by its ID.
    """
    session = SessionLocal()
    try:
        problem = session.query(Problem).get(problem_id)
        if not problem:
            return jsonify({"error": "Problem not found"}), 404
        return jsonify(problem.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    """
    Create a new problem.
    """
    session = SessionLocal()
    try:
        data = request.json
        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty')
        )
        session.add(new_problem)
        session.commit()
        return jsonify(new_problem.to_dict()), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """
    Update an existing problem by its ID.
    """
    session = SessionLocal()
    try:
        data = request.json
        problem = session.query(Problem).get(problem_id)
        if not problem:
            return jsonify({"error": "Problem not found"}), 404

        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)

        session.commit()
        return jsonify(problem.to_dict()), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """
    Delete a problem by its ID.
    """
    session = SessionLocal()
    try:
        problem = session.query(Problem).get(problem_id)
        if not problem:
            return jsonify({"error": "Problem not found"}), 404

        session.delete(problem)
        session.commit()
        return jsonify({"message": "Problem deleted successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()