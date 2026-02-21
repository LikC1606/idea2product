from flask import Blueprint, jsonify, request
from app.database import get_db_session
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_all_problems():
    """
    Fetch all problems from the database.
    """
    session = get_db_session()
    try:
        problems = session.query(Problem).all()
        problems_data = [problem.to_dict() for problem in problems]
        return jsonify(problems_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """
    Fetch a single problem by its ID.
    """
    session = get_db_session()
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        return jsonify(problem.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    """
    Create a new problem.
    """
    session = get_db_session()
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
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """
    Update an existing problem.
    """
    session = get_db_session()
    try:
        data = request.json
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        
        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        
        session.commit()
        return jsonify(problem.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """
    Delete a problem by its ID.
    """
    session = get_db_session()
    try:
        problem = session.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        
        session.delete(problem)
        session.commit()
        return jsonify({'message': 'Problem deleted successfully'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()