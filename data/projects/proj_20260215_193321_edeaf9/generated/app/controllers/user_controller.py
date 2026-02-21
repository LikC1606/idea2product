from flask import Blueprint, request, jsonify
from app.database import db
from app.models.problem import Problem

user_bp = Blueprint('user', __name__)

@user_bp.route('/users/<int:user_id>/problems', methods=['GET'])
def get_user_problems(user_id):
    """
    Retrieve all problems solved by a specific user.
    """
    try:
        problems = Problem.query.filter_by(user_id=user_id).all()
        return jsonify([problem.to_dict() for problem in problems]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>/problems/<int:problem_id>', methods=['POST'])
def solve_problem(user_id, problem_id):
    """
    Mark a problem as solved by a user.
    """
    try:
        problem = Problem.query.filter_by(id=problem_id).first()
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        
        # Assume there's a method to mark a problem as solved in the Problem model
        problem.mark_as_solved(user_id)
        db.session.commit()
        return jsonify({'message': 'Problem marked as solved'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500