from flask import Blueprint, request, jsonify
from app.models.solution import Solution
from app import db  # Assuming db is imported from app

def solution_blueprint():
    solution_bp = Blueprint('solution', __name__)

    @solution_bp.route('/solutions', methods=['GET'])
    def get_solutions():
        try:
            solutions = Solution.query.all()
            return jsonify([solution.to_dict() for solution in solutions]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404
            return jsonify(solution.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @solution_bp.route('/solutions', methods=['POST'])
    def create_solution():
        try:
            data = request.get_json()
            new_solution = Solution(**data)
            db.session.add(new_solution)
            db.session.commit()
            return jsonify(new_solution.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
    def update_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404

            data = request.get_json()
            for key, value in data.items():
                setattr(solution, key, value)
            db.session.add(solution)
            db.session.commit()
            return jsonify(solution.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
    def delete_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404

            db.session.delete(solution)
            db.session.commit()
            return jsonify({'message': 'Solution deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return solution_bp