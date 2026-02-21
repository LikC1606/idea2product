from flask import Blueprint, request, jsonify
from app.controllers.problem_controller import (
    get_problems,
    get_problem,
    create_problem,
    update_problem,
    delete_problem,
)

# Define blueprint for problem routes
problem_routes_bp = Blueprint('problem_routes', __name__)

# Route to get all problems
@problem_routes_bp.route('/problems', methods=['GET'])
def list_problems():
    try:
        problems = get_problems()
        return jsonify(problems), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to get a specific problem by ID
@problem_routes_bp.route('/problems/<int:problem_id>', methods=['GET'])
def retrieve_problem(problem_id):
    try:
        problem = get_problem(problem_id)
        if problem:
            return jsonify(problem), 200
        return jsonify({'error': 'Problem not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to create a new problem
@problem_routes_bp.route('/problems', methods=['POST'])
def add_problem():
    try:
        problem_data = request.json
        if not problem_data or 'title' not in problem_data or 'description' not in problem_data:
            return jsonify({'error': 'Invalid input, title and description are required'}), 400
        new_problem = create_problem(problem_data)
        return jsonify(new_problem), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to update an existing problem
@problem_routes_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def modify_problem(problem_id):
    try:
        problem_data = request.json
        if not problem_data:
            return jsonify({'error': 'Invalid input, no data provided'}), 400
        updated_problem = update_problem(problem_id, problem_data)
        if updated_problem:
            return jsonify(updated_problem), 200
        return jsonify({'error': 'Problem not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to delete a problem
@problem_routes_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def remove_problem(problem_id):
    try:
        result = delete_problem(problem_id)
        if result:
            return jsonify({'message': 'Problem deleted successfully'}), 200
        return jsonify({'error': 'Problem not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500