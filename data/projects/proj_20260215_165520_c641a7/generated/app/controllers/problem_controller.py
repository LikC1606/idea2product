from flask import Blueprint, jsonify, request
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    # Route for getting all problems
    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        problems = Problem.query.all()
        return jsonify([problem.to_dict() for problem in problems]), 200

    # Route for getting a specific problem by ID
    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        return jsonify(problem.to_dict()), 200

    # Route for creating a new problem
    @blueprint.route('/problems', methods=['POST'])
    def create_problem():
        data = request.json
        if not data or not data.get('title') or not data.get('description'):
            return jsonify({'error': 'Invalid data'}), 400
        
        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty', 'Easy')
        )
        new_problem.save()
        return jsonify(new_problem.to_dict()), 201

    # Route for updating a problem
    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid data'}), 400
        
        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        problem.save()
        return jsonify(problem.to_dict()), 200

    # Route for deleting a problem
    @blueprint.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        
        problem.delete()
        return jsonify({'message': 'Problem deleted successfully'}), 200

    return blueprint