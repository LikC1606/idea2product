from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def get_solutions():
    """
    Retrieve all solutions.
    """
    session = SessionLocal()
    try:
        solutions = session.query(Solution).all()
        solution_list = [
            {
                'id': solution.id,
                'code': solution.code,
                'language': solution.language,
                'status': solution.status,
                'user_id': solution.user_id,
                'problem_id': solution.problem_id
            }
            for solution in solutions
        ]
        return jsonify(solution_list), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    """
    Retrieve a solution by ID.
    """
    session = SessionLocal()
    try:
        solution = session.query(Solution).filter(Solution.id == solution_id).first()
        if solution:
            solution_data = {
                'id': solution.id,
                'code': solution.code,
                'language': solution.language,
                'status': solution.status,
                'user_id': solution.user_id,
                'problem_id': solution.problem_id
            }
            return jsonify(solution_data), 200
        else:
            return jsonify({'error': 'Solution not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    """
    Create a new solution.
    """
    session = SessionLocal()
    try:
        data = request.json
        new_solution = Solution(
            code=data['code'],
            language=data['language'],
            status=data.get('status', 'pending'),
            user_id=data['user_id'],
            problem_id=data['problem_id']
        )
        session.add(new_solution)
        session.commit()
        return jsonify({'message': 'Solution created successfully', 'id': new_solution.id}), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """
    Update an existing solution.
    """
    session = SessionLocal()
    try:
        data = request.json
        solution = session.query(Solution).filter(Solution.id == solution_id).first()
        if solution:
            solution.code = data.get('code', solution.code)
            solution.language = data.get('language', solution.language)
            solution.status = data.get('status', solution.status)
            solution.user_id = data.get('user_id', solution.user_id)
            solution.problem_id = data.get('problem_id', solution.problem_id)
            session.commit()
            return jsonify({'message': 'Solution updated successfully'}), 200
        else:
            return jsonify({'error': 'Solution not found'}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """
    Delete a solution.
    """
    session = SessionLocal()
    try:
        solution = session.query(Solution).filter(Solution.id == solution_id).first()
        if solution:
            session.delete(solution)
            session.commit()
            return jsonify({'message': 'Solution deleted successfully'}), 200
        else:
            return jsonify({'error': 'Solution not found'}), 404
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()