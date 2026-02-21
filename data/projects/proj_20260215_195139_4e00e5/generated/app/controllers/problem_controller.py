from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = Problem.query.all()
        problem_list = [
            {
                'id': problem.id,
                'title': problem.title,
                'description': problem.description,
                'difficulty': problem.difficulty
            }
            for problem in problems
        ]
        return jsonify({'problems': problem_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem is None:
            return jsonify({'error': 'Problem not found'}), 404
        problem_data = {
            'id': problem.id,
            'title': problem.title,
            'description': problem.description,
            'difficulty': problem.difficulty
        }
        return jsonify({'problem': problem_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        difficulty = data.get('difficulty')

        if not title or not description or not difficulty:
            return jsonify({'error': 'Missing required fields'}), 400

        new_problem = Problem(title=title, description=description, difficulty=difficulty)
        db.session.add(new_problem)
        db.session.commit()

        return jsonify({'message': 'Problem created successfully', 'problem_id': new_problem.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        data = request.get_json()
        problem = Problem.query.get(problem_id)

        if problem is None:
            return jsonify({'error': 'Problem not found'}), 404

        title = data.get('title')
        description = data.get('description')
        difficulty = data.get('difficulty')

        if title:
            problem.title = title
        if description:
            problem.description = description
        if difficulty:
            problem.difficulty = difficulty

        db.session.commit()

        return jsonify({'message': 'Problem updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)

        if problem is None:
            return jsonify({'error': 'Problem not found'}), 404

        db.session.delete(problem)
        db.session.commit()

        return jsonify({'message': 'Problem deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500