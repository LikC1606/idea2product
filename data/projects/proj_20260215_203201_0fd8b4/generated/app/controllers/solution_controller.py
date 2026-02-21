from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
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
    db: Session = SessionLocal()
    try:
        solutions = db.query(Solution).all()
        return jsonify([{
            'id': solution.id,
            'code': solution.code,
            'language': solution.language,
            'status': solution.status,
            'user_id': solution.user_id,
            'problem_id': solution.problem_id
        } for solution in solutions]), 200
    finally:
        db.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    """
    Retrieve a specific solution by ID.
    """
    db: Session = SessionLocal()
    try:
        solution = db.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        return jsonify({
            'id': solution.id,
            'code': solution.code,
            'language': solution.language,
            'status': solution.status,
            'user_id': solution.user_id,
            'problem_id': solution.problem_id
        }), 200
    finally:
        db.close()

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    """
    Create a new solution.
    """
    db: Session = SessionLocal()
    try:
        data = request.json
        user_id = data.get('user_id')
        problem_id = data.get('problem_id')

        # Validate the user and problem exist
        user = db.query(User).filter(User.id == user_id).first()
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404

        # Create solution
        solution = Solution(
            code=data.get('code'),
            language=data.get('language'),
            status=data.get('status'),
            user_id=user_id,
            problem_id=problem_id
        )
        db.add(solution)
        db.commit()
        db.refresh(solution)

        return jsonify({
            'id': solution.id,
            'code': solution.code,
            'language': solution.language,
            'status': solution.status,
            'user_id': solution.user_id,
            'problem_id': solution.problem_id
        }), 201
    finally:
        db.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """
    Update an existing solution.
    """
    db: Session = SessionLocal()
    try:
        data = request.json
        solution = db.query(Solution).filter(Solution.id == solution_id).first()

        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        # Update fields
        solution.code = data.get('code', solution.code)
        solution.language = data.get('language', solution.language)
        solution.status = data.get('status', solution.status)
        db.commit()
        db.refresh(solution)

        return jsonify({
            'id': solution.id,
            'code': solution.code,
            'language': solution.language,
            'status': solution.status,
            'user_id': solution.user_id,
            'problem_id': solution.problem_id
        }), 200
    finally:
        db.close()

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """
    Delete a solution from the database.
    """
    db: Session = SessionLocal()
    try:
        solution = db.query(Solution).filter(Solution.id == solution_id).first()
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        db.delete(solution)
        db.commit()
        return jsonify({'message': 'Solution deleted successfully'}), 200
    finally:
        db.close()