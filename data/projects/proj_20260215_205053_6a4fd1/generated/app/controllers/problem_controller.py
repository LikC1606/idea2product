from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    """
    Fetch all problems from the database.
    Returns a list of problems in JSON format.
    """
    try:
        problems = Problem.query.all()
        problem_list = [problem.to_dict() for problem in problems]
        return jsonify(problem_list), 200
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching problems.", "message": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Fetch a specific problem by its ID.
    Returns the problem data in JSON format.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"error": "Problem not found."}), 404
        return jsonify(problem.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching the problem.", "message": str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    """
    Create a new problem in the database.
    Accepts problem data in JSON format.
    """
    try:
        data = request.json
        new_problem = Problem(**data)
        db.session.add(new_problem)
        db.session.commit()
        return jsonify(new_problem.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while creating the problem.", "message": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """
    Update an existing problem in the database.
    Accepts updated problem data in JSON format.
    """
    try:
        data = request.json
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"error": "Problem not found."}), 404
        for key, value in data.items():
            setattr(problem, key, value)
        db.session.commit()
        return jsonify(problem.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while updating the problem.", "message": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """
    Delete a specific problem by its ID from the database.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"error": "Problem not found."}), 404
        db.session.delete(problem)
        db.session.commit()
        return jsonify({"message": "Problem deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while deleting the problem.", "message": str(e)}), 500