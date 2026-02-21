from flask import Blueprint, jsonify, request
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        # Simulated query for all problems (replace with actual DB query as needed)
        problems = Problem.query.all()
        return jsonify([problem.to_dict() for problem in problems]), 200

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Simulated query for a single problem by ID
        problem = Problem.query.get(problem_id)
        if problem:
            return jsonify(problem.to_dict()), 200
        return jsonify({'error': 'Problem not found'}), 404

    @blueprint.route('/problems', methods=['POST'])
    def create_problem():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        try:
            # Simulated creation of a new problem
            new_problem = Problem(
                title=data.get('title'),
                description=data.get('description'),
                difficulty=data.get('difficulty')
            )
            new_problem.save()  # Replace with actual DB save logic
            return jsonify(new_problem.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        try:
            # Simulated update of a problem
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            problem.save()  # Replace with actual DB update logic
            return jsonify(problem.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        try:
            # Simulated deletion of a problem
            problem.delete()  # Replace with actual DB delete logic
            return jsonify({'message': 'Problem deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return blueprint