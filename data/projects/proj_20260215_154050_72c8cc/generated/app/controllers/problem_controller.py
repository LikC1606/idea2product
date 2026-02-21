from flask import Blueprint, request, jsonify
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problems', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        # Retrieve all problems
        problems = Problem.query.all()
        problems_list = [problem.to_dict() for problem in problems]
        return jsonify(problems_list), 200

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Retrieve a single problem by id
        problem = Problem.query.get(problem_id)
        if problem is None:
            return jsonify({'error': 'Problem not found'}), 404
        return jsonify(problem.to_dict()), 200

    @blueprint.route('/problems', methods=['POST'])
    def create_problem():
        # Create a new problem
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400

        try:
            problem = Problem(**data)
            problem.save()
            return jsonify(problem.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        # Update an existing problem
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400

        problem = Problem.query.get(problem_id)
        if problem is None:
            return jsonify({'error': 'Problem not found'}), 404

        try:
            for key, value in data.items():
                setattr(problem, key, value)
            problem.save()
            return jsonify(problem.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        # Delete a problem by id
        problem = Problem.query.get(problem_id)
        if problem is None:
            return jsonify({'error': 'Problem not found'}), 404

        try:
            problem.delete()
            return jsonify({'message': 'Problem deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return blueprint