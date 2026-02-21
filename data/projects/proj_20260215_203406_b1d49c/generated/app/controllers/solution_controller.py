from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def get_all_solutions():
    """Fetch all solutions from the database."""
    db: Session = next(get_db())
    solutions = db.query(Solution).all()
    return jsonify([{
        "id": solution.id,
        "user_id": solution.user_id,
        "problem_id": solution.problem_id,
        "code": solution.code,
        "created_at": solution.created_at
    } for solution in solutions]), 200

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    """Fetch a specific solution by its ID."""
    db: Session = next(get_db())
    solution = db.query(Solution).filter(Solution.id == solution_id).first()
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    return jsonify({
        "id": solution.id,
        "user_id": solution.user_id,
        "problem_id": solution.problem_id,
        "code": solution.code,
        "created_at": solution.created_at
    }), 200

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    """Create a new solution."""
    db: Session = next(get_db())
    data = request.get_json()

    # Validate required fields
    user_id = data.get('user_id')
    problem_id = data.get('problem_id')
    code = data.get('code')

    if not user_id or not problem_id or not code:
        return jsonify({"error": "user_id, problem_id, and code are required"}), 400

    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check if problem exists
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        return jsonify({"error": "Problem not found"}), 404

    # Create the solution
    solution = Solution(user_id=user_id, problem_id=problem_id, code=code)
    db.add(solution)
    db.commit()
    db.refresh(solution)

    return jsonify({
        "id": solution.id,
        "user_id": solution.user_id,
        "problem_id": solution.problem_id,
        "code": solution.code,
        "created_at": solution.created_at
    }), 201

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """Update an existing solution."""
    db: Session = next(get_db())
    solution = db.query(Solution).filter(Solution.id == solution_id).first()
    if not solution:
        return jsonify({"error": "Solution not found"}), 404

    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({"error": "code field is required"}), 400

    solution.code = code
    db.commit()
    db.refresh(solution)

    return jsonify({
        "id": solution.id,
        "user_id": solution.user_id,
        "problem_id": solution.problem_id,
        "code": solution.code,
        "created_at": solution.created_at
    }), 200

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """Delete a solution by its ID."""
    db: Session = next(get_db())
    solution = db.query(Solution).filter(Solution.id == solution_id).first()
    if not solution:
        return jsonify({"error": "Solution not found"}), 404

    db.delete(solution)
    db.commit()

    return jsonify({"message": "Solution deleted successfully"}), 200