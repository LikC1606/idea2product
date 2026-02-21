from flask import Blueprint, jsonify, request

def problem_bp():
    problem_blueprint = Blueprint('problem', __name__)

    @problem_blueprint.route('/problems', methods=['GET'])
    def get_problems():
        # Placeholder for fetching problems from the database
        problems = []  # No database access per specification
        return jsonify(problems), 200

    @problem_blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Placeholder for fetching a single problem by ID
        problem = None  # No database access per specification
        if problem:
            return jsonify(problem), 200
        return jsonify({'error': 'Problem not found'}), 404

    @problem_blueprint.route('/problems', methods=['POST'])
    def create_problem():
        # Placeholder for creating a new problem (no database operations allowed)
        data = request.get_json()
        if not data or 'title' not in data or 'description' not in data:
            return jsonify({'error': 'Invalid input'}), 400
        # Returning a mock problem creation response
        new_problem = {
            'id': 1,  # Mock ID
            'title': data['title'],
            'description': data['description']
        }
        return jsonify(new_problem), 201

    return problem_blueprint