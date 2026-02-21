from flask import Blueprint, jsonify
from app.models.problem import Problem
from app.database import db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = Problem.query.all()
        problem_list = [{'id': problem.id, 'title': problem.title, 'description': problem.description} for problem in problems]
        return jsonify({'problems': problem_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem_by_id(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem:
            problem_data = {'id': problem.id, 'title': problem.title, 'description': problem.description}
            return jsonify({'problem': problem_data}), 200
        else:
            return jsonify({'error': 'Problem not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    try:
        # Example data parsing, assuming JSON input
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')

        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400

        new_problem = Problem(title=title, description=description)
        db.session.add(new_problem)
        db.session.commit()

        return jsonify({'message': 'Problem created successfully', 'problem': {'id': new_problem.id, 'title': new_problem.title, 'description': new_problem.description}}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500