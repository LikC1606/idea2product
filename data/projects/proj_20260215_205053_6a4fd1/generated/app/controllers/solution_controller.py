from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User
from app.database import db

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['POST'])
def create_solution():
    """
    Create a new solution for a problem by a user.
    Expects JSON data with 'problem_id', 'user_id', and 'content'.
    """
    data = request.get_json()
    problem_id = data.get('problem_id')
    user_id = data.get('user_id')
    content = data.get('content')
    
    if not problem_id or not user_id or not content:
        return jsonify({"error": "Missing required fields"}), 400

    # Validate existence of problem and user
    problem = Problem.get_by_id(problem_id)
    user = User.get_by_id(user_id)
    
    if not problem:
        return jsonify({"error": "Problem not found"}), 404
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Create and save solution
    solution = Solution(problem_id=problem_id, user_id=user_id, content=content)
    db.session.add(solution)
    db.session.commit()
    return jsonify({"message": "Solution created successfully", "solution_id": solution.id}), 201

@solution_bp.route('/solutions/<solution_id>', methods=['GET'])
def get_solution(solution_id):
    """
    Retrieve a solution by its ID.
    """
    solution = Solution.get_by_id(solution_id)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    
    return jsonify({
        "id": solution.id,
        "problem_id": solution.problem_id,
        "user_id": solution.user_id,
        "content": solution.content
    }), 200

@solution_bp.route('/solutions/user/<user_id>', methods=['GET'])
def get_solutions_by_user(user_id):
    """
    Retrieve all solutions submitted by a specific user.
    """
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    solutions = Solution.get_all_by_user(user_id)
    return jsonify([
        {
            "id": solution.id,
            "problem_id": solution.problem_id,
            "content": solution.content
        } for solution in solutions
    ]), 200

@solution_bp.route('/solutions/problem/<problem_id>', methods=['GET'])
def get_solutions_by_problem(problem_id):
    """
    Retrieve all solutions submitted for a specific problem.
    """
    problem = Problem.get_by_id(problem_id)
    if not problem:
        return jsonify({"error": "Problem not found"}), 404
    
    solutions = Solution.get_all_by_problem(problem_id)
    return jsonify([
        {
            "id": solution.id,
            "user_id": solution.user_id,
            "content": solution.content
        } for solution in solutions
    ]), 200

@solution_bp.route('/solutions/<solution_id>', methods=['PUT'])
def update_solution(solution_id):
    """
    Update the content of an existing solution.
    Expects JSON data with 'content'.
    """
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({"error": "Missing content"}), 400
    
    solution = Solution.get_by_id(solution_id)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    
    solution.content = content
    db.session.commit()
    return jsonify({"message": "Solution updated successfully"}), 200

@solution_bp.route('/solutions/<solution_id>', methods=['DELETE'])
def delete_solution(solution_id):
    """
    Delete a solution by its ID.
    """
    solution = Solution.get_by_id(solution_id)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    
    db.session.delete(solution)
    db.session.commit()
    return jsonify({"message": "Solution deleted successfully"}), 200