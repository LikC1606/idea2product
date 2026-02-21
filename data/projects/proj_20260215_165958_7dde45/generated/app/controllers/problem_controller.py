from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        try:
            problems = Problem.query.all()
            problems_data = [{'id': p.id, 'title': p.title, 'description': p.description} for p in problems]
            return jsonify({'problems': problems_data}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if problem:
                problem_data = {'id': problem.id, 'title': problem.title, 'description': problem.description}
                return jsonify({'problem': problem_data}), 200
            else:
                return jsonify({'error': 'Problem not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/problems', methods=['POST'])
    def create_problem():
        try:
            data = request.json
            new_problem = Problem(title=data['title'], description=data['description'])
            db.session.add(new_problem)
            db.session.commit()
            return jsonify({'message': 'Problem created successfully', 'problem_id': new_problem.id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            data = request.json
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            db.session.commit()
            return jsonify({'message': 'Problem updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['DELETE'])
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

    return blueprint