from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db

def problem_blueprint():
    problem_bp = Blueprint('problem', __name__)

    @problem_bp.route('/problems', methods=['GET'])
    def get_problems():
        problems = Problem.query.all()
        problems_data = [{'id': p.id, 'title': p.title, 'description': p.description} for p in problems]
        return jsonify(problems_data), 200

    @problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        problem_data = {'id': problem.id, 'title': problem.title, 'description': problem.description}
        return jsonify(problem_data), 200

    @problem_bp.route('/problems', methods=['POST'])
    def create_problem():
        data = request.get_json()
        if not data or not all(key in data for key in ('title', 'description')):
            return jsonify({'error': 'Invalid data'}), 400
        new_problem = Problem(title=data['title'], description=data['description'])
        db.session.add(new_problem)
        db.session.commit()
        return jsonify({'message': 'Problem created successfully', 'id': new_problem.id}), 201

    @problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        if 'title' in data:
            problem.title = data['title']
        if 'description' in data:
            problem.description = data['description']
        db.session.commit()
        return jsonify({'message': 'Problem updated successfully'}), 200

    @problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        db.session.delete(problem)
        db.session.commit()
        return jsonify({'message': 'Problem deleted successfully'}), 200

    return problem_bp