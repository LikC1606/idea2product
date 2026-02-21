from flask import Blueprint, jsonify, request, abort
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    """
    Retrieve all problems from the database.
    """
    db: Session = get_db()
    try:
        problems = db.query(Problem).all()
        return jsonify([problem.to_dict() for problem in problems])
    except Exception as e:
        abort(500, description=str(e))


@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Retrieve a specific problem by its ID.
    """
    db: Session = get_db()
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            abort(404, description="Problem not found")
        return jsonify(problem.to_dict())
    except Exception as e:
        abort(500, description=str(e))


@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    """
    Create a new problem in the database.
    """
    db: Session = get_db()
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'description' not in data:
            abort(400, description="Missing required fields: title, description")

        new_problem = Problem(
            title=data['title'],
            description=data['description'],
            difficulty=data.get('difficulty', 'Medium')  # Default difficulty: Medium
        )
        db.add(new_problem)
        db.commit()
        db.refresh(new_problem)
        return jsonify(new_problem.to_dict()), 201
    except Exception as e:
        db.rollback()
        abort(500, description=str(e))


@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """
    Update an existing problem in the database.
    """
    db: Session = get_db()
    try:
        data = request.get_json()
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            abort(404, description="Problem not found")

        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)

        db.commit()
        db.refresh(problem)
        return jsonify(problem.to_dict())
    except Exception as e:
        db.rollback()
        abort(500, description=str(e))


@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """
    Delete a problem from the database.
    """
    db: Session = get_db()
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            abort(404, description="Problem not found")

        db.delete(problem)
        db.commit()
        return jsonify({"message": "Problem deleted successfully"})
    except Exception as e:
        db.rollback()
        abort(500, description=str(e))