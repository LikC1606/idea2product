from flask import Blueprint, request, jsonify, abort
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def get_solutions():
    """
    Retrieve all solutions from the database.
    """
    db = SessionLocal()
    try:
        solutions = db.query(Solution).all()
        return jsonify([solution.to_dict() for solution in solutions]), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    """
    Retrieve a specific solution by its ID.
    """
    db = SessionLocal()
    try:
        solution = db.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            abort(404, description="Solution not found")
        return jsonify(solution.to_dict()), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    """
    Create a new solution in the database.
    """
    db = SessionLocal()
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        problem_id = data.get('problem_id')
        code = data.get('code')

        if not user_id or not problem_id or not code:
            abort(400, description="Missing required fields: 'user_id', 'problem_id', 'code'")

        user = db.query(User).filter(User.id == user_id).first()
        problem = db.query(Problem).filter(Problem.id == problem_id).first()

        if not user or not problem:
            abort(404, description="User or Problem not found")

        new_solution = Solution(user_id=user_id, problem_id=problem_id, code=code)
        db.add(new_solution)
        db.commit()
        db.refresh(new_solution)
        return jsonify(new_solution.to_dict()), 201
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """
    Update an existing solution by its ID.
    """
    db = SessionLocal()
    try:
        data = request.get_json()
        code = data.get('code')

        if not code:
            abort(400, description="Missing required field: 'code'")

        solution = db.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            abort(404, description="Solution not found")

        solution.code = code
        db.commit()
        return jsonify(solution.to_dict()), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """
    Delete a solution by its ID.
    """
    db = SessionLocal()
    try:
        solution = db.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            abort(404, description="Solution not found")

        db.delete(solution)
        db.commit()
        return jsonify({'message': 'Solution deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()