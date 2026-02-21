from flask import Blueprint, request, jsonify
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        # Assuming Problem has a method to get all problems
        problems = Problem.get_all_problems()
        return jsonify([problem.to_dict() for problem in problems]), 200

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Assuming Problem has a method to find a problem by its ID
        problem = Problem.find_by_id(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        return jsonify(problem.to_dict()), 200

    @blueprint.route('/problems', methods=['POST'])
    def create_problem():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400

        try:
            # Assuming Problem has a method to create a new problem
            new_problem = Problem.create_problem(data)
            return jsonify(new_problem.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400

        # Assuming Problem has a method to find and update a problem by its ID
        problem = Problem.find_by_id(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404

        try:
            updated_problem = problem.update(data)
            return jsonify(updated_problem.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        # Assuming Problem has a method to find and delete a problem by its ID
        problem = Problem.find_by_id(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404

        try:
            db.session.delete(problem)
            db.session.commit()
            return jsonify({'message': 'Problem deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return blueprint