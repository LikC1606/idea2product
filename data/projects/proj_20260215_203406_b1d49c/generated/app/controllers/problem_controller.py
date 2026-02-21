from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_all_problems():
    """Retrieve all problems from the database."""
    db = get_db()
    try:
        problems = db.query(Problem).all()
        result = [problem.to_dict() for problem in problems]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """Retrieve a specific problem by ID."""
    db = get_db()
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            return jsonify(problem.to_dict()), 200
        else:
            return jsonify({"error": "Problem not found"}), 404
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    """Create a new problem."""
    db = get_db()
    try:
        data = request.json
        new_problem = Problem(**data)
        db.add(new_problem)
        db.commit()
        return jsonify(new_problem.to_dict()), 201
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """Update an existing problem."""
    db = get_db()
    try:
        data = request.json
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            for key, value in data.items():
                setattr(problem, key, value)
            db.commit()
            return jsonify(problem.to_dict()), 200
        else:
            return jsonify({"error": "Problem not found"}), 404
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """Delete a problem."""
    db = get_db()
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if problem:
            db.delete(problem)
            db.commit()
            return jsonify({"message": "Problem deleted successfully"}), 200
        else:
            return jsonify({"error": "Problem not found"}), 404
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500