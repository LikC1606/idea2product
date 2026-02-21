from flask import Blueprint, request, jsonify
from app.models.problem import Problem
from app.database import db

problem_controller = Blueprint('problem_controller', __name__)

# Route to fetch all problems
@problem_controller.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = Problem.query.all()
        result = [problem.to_dict() for problem in problems]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to fetch a specific problem
@problem_controller.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        return jsonify(problem.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to create a new problem
@problem_controller.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.get_json()
        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty')
        )
        db.session.add(new_problem)
        db.session.commit()
        return jsonify({'message': 'Problem created successfully', 'problem': new_problem.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Route to update an existing problem
@problem_controller.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        data = request.get_json()
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        db.session.commit()
        return jsonify({'message': 'Problem updated successfully', 'problem': problem.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Route to delete a problem
@problem_controller.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        db.session.delete(problem)
        db.session.commit()
        return jsonify({'message': 'Problem deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500