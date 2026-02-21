from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db

def problem_bp():
    blueprint = Blueprint('problem', __name__, url_prefix='/problems')

    @blueprint.route('/', methods=['GET'])
    def get_problems():
        try:
            problems = Problem.query.all()
            problems_data = [problem.to_dict() for problem in problems]
            return jsonify({'problems': problems_data}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            return jsonify({'problem': problem.to_dict()}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/', methods=['POST'])
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
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            
            data = request.get_json()
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            
            db.session.commit()
            return jsonify({'message': 'Problem updated successfully', 'problem': problem.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/<int:problem_id>', methods=['DELETE'])
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
            return jsonify({'error': str(e)}), 400

    return blueprint