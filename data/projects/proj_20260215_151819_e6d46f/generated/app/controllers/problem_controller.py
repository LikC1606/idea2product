from flask import Blueprint, request, jsonify
from app.models.problem import Problem

def problem_blueprint():
    problem_bp = Blueprint('problem', __name__)

    @problem_bp.route('/problems', methods=['GET'])
    def get_problems():
        try:
            problems = Problem.query.all()
            return jsonify([problem.to_dict() for problem in problems]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404
            return jsonify(problem.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @problem_bp.route('/problems', methods=['POST'])
    def create_problem():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid input'}), 400
            
            new_problem = Problem(**data)
            new_problem.save()
            return jsonify(new_problem.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid input'}), 400

            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404

            for key, value in data.items():
                setattr(problem, key, value)
            problem.save()
            return jsonify(problem.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'error': 'Problem not found'}), 404

            problem.delete()
            return jsonify({'message': 'Problem deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return problem_bp