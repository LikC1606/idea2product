from flask import Blueprint, jsonify
from app.models.problem import Problem
from app.database import db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    problems = Problem.query.all()
    problems_data = [{'id': p.id, 'title': p.title, 'description': p.description} for p in problems]
    return jsonify(problems_data)

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if problem is None:
        return jsonify({'error': 'Problem not found'}), 404
    problem_data = {'id': problem.id, 'title': problem.title, 'description': problem.description}
    return jsonify(problem_data)