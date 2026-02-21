from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app import db  # Ensure db is imported

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        try:
            problems = Problem.query.all()
            return jsonify([problem.to_dict() for problem in problems]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            return jsonify(problem.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/problems', methods=['POST'])
    def create_problem():
        try:
            data = request.get_json()
            problem = Problem(**data)
            db.session.add(problem)
            db.session.commit()
            return jsonify(problem.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        try:
            data = request.get_json()
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            for key, value in data.items():
                setattr(problem, key, value)
            db.session.add(problem)
            db.session.commit()
            return jsonify(problem.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            db.session.delete(problem)
            db.session.commit()
            return jsonify({'message': 'Problem deleted'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return blueprint