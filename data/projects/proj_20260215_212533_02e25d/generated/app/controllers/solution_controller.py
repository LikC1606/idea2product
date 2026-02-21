from flask import Blueprint, request, jsonify, render_template
from app.database import db
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def list_solutions():
    """
    Endpoint to list all solutions in the database.
    """
    solutions = Solution.query.all()
    return jsonify([{
        'id': solution.id,
        'code': solution.code,
        'language': solution.language,
        'user_id': solution.user_id,
        'problem_id': solution.problem_id
    } for solution in solutions])

@solution_bp.route('/solution/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    """
    Endpoint to view a specific solution by ID.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404
    return jsonify({
        'id': solution.id,
        'code': solution.code,
        'language': solution.language,
        'user_id': solution.user_id,
        'problem_id': solution.problem_id
    })

@solution_bp.route('/solution/new', methods=['POST'])
def create_solution():
    """
    Endpoint to create a new solution.
    """
    data = request.json
    code = data.get('code')
    language = data.get('language')
    user_id = data.get('user_id')
    problem_id = data.get('problem_id')

    # Validate user and problem existence
    user = User.query.get(user_id)
    problem = Problem.query.get(problem_id)
    if not user or not problem:
        return jsonify({'error': 'Invalid user or problem ID'}), 400

    # Create and save new solution
    solution = Solution(code=code, language=language, user_id=user_id, problem_id=problem_id)
    db.session.add(solution)
    db.session.commit()

    return jsonify({'message': 'Solution created', 'solution_id': solution.id}), 201

@solution_bp.route('/solution/<int:solution_id>/edit', methods=['PUT'])
def edit_solution(solution_id):
    """
    Endpoint to edit an existing solution.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    data = request.json
    solution.code = data.get('code', solution.code)
    solution.language = data.get('language', solution.language)
    db.session.commit()

    return jsonify({'message': 'Solution updated', 'solution_id': solution.id})

@solution_bp.route('/solution/<int:solution_id>/delete', methods=['DELETE'])
def delete_solution(solution_id):
    """
    Endpoint to delete a solution by ID.
    """
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404

    db.session.delete(solution)
    db.session.commit()

    return jsonify({'message': 'Solution deleted'})