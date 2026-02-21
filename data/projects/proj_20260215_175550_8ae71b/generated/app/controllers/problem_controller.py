from flask import Blueprint, request, jsonify
from app.models.problem import Problem
from app import db

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_all_problems():
        try:
            problems = Problem.query.all()
            problems_list = [problem.to_dict() for problem in problems]
            return jsonify(problems_list), 200
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
            new_problem = Problem(
                title=data.get('title'),
                description=data.get('description'),
                difficulty=data.get('difficulty')
            )
            db.session.add(new_problem)
            db.session.commit()
            return jsonify(new_problem.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404

            data = request.get_json()
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            db.session.add(problem)
            db.session.commit()

            return jsonify(problem.to_dict()), 200
        except Exception as e:
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
            return jsonify({'error': str(e)}), 500

    return blueprint