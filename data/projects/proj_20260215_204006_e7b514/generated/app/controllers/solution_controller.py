from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db_session
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def get_all_solutions():
    """Retrieve all solutions."""
    session = get_db_session()
    try:
        solutions = session.query(Solution).all()
        result = [solution.to_dict() for solution in solutions]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    """Retrieve a specific solution by ID."""
    session = get_db_session()
    try:
        solution = session.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        return jsonify(solution.to_dict()), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    """Create a new solution."""
    session = get_db_session()
    data = request.get_json()
    try:
        # Validate required fields
        problem_id = data.get('problem_id')
        user_id = data.get('user_id')
        code = data.get('code')
        if not (problem_id and user_id and code):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if problem and user exist
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        user = session.query(User).filter(User.id == user_id).first()
        if not problem or not user:
            return jsonify({'error': 'Invalid problem or user ID'}), 400

        # Create and save the solution
        new_solution = Solution(problem_id=problem_id, user_id=user_id, code=code)
        session.add(new_solution)
        session.commit()
        return jsonify(new_solution.to_dict()), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """Update an existing solution."""
    session = get_db_session()
    data = request.get_json()
    try:
        solution = session.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        # Update fields if present in the request
        if 'code' in data:
            solution.code = data['code']
        session.commit()
        return jsonify(solution.to_dict()), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """Delete a solution."""
    session = get_db_session()
    try:
        solution = session.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        session.delete(solution)
        session.commit()
        return jsonify({'message': 'Solution deleted successfully'}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()