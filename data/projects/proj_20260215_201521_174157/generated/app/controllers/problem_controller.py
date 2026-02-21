from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Problem
from app.utils import authenticate_user

# Must Export
problem_bp = Blueprint('problem', __name__)

# Routes

@problem_bp.route('/problems', methods=['GET'])
def get_all_problems():
    """
    Fetch all problems from the database.
    """
    try:
        problems = Problem.query.all()
        problem_list = [
            {
                "id": problem.id,
                "title": problem.title,
                "difficulty": problem.difficulty,
                "description": problem.description,
            }
            for problem in problems
        ]
        return jsonify({"success": True, "data": problem_list}), 200
    except SQLAlchemyError as e:
        return jsonify({"success": False, "error": str(e)}), 500


@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Fetch a single problem by its ID.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"success": False, "error": "Problem not found"}), 404

        problem_data = {
            "id": problem.id,
            "title": problem.title,
            "difficulty": problem.difficulty,
            "description": problem.description,
            "hints": problem.hints,
        }
        return jsonify({"success": True, "data": problem_data}), 200
    except SQLAlchemyError as e:
        return jsonify({"success": False, "error": str(e)}), 500


@problem_bp.route('/problems', methods=['POST'])
@authenticate_user
def create_problem():
    """
    Create a new problem.
    """
    try:
        data = request.get_json()
        title = data.get('title')
        difficulty = data.get('difficulty')
        description = data.get('description')
        hints = data.get('hints')

        if not title or not difficulty or not description:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        new_problem = Problem(
            title=title,
            difficulty=difficulty,
            description=description,
            hints=hints
        )
        db.session.add(new_problem)
        db.session.commit()

        return jsonify({"success": True, "data": {"id": new_problem.id}}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
@authenticate_user
def update_problem(problem_id):
    """
    Update an existing problem.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"success": False, "error": "Problem not found"}), 404

        data = request.get_json()
        problem.title = data.get('title', problem.title)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        problem.description = data.get('description', problem.description)
        problem.hints = data.get('hints', problem.hints)

        db.session.commit()

        return jsonify({"success": True, "data": {"id": problem.id}}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
@authenticate_user
def delete_problem(problem_id):
    """
    Delete a problem by its ID.
    """
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"success": False, "error": "Problem not found"}), 404

        db.session.delete(problem)
        db.session.commit()

        return jsonify({"success": True, "message": "Problem deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500