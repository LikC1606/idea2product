from flask import Blueprint, jsonify, request
from app.models.solution import Solution
from app.database import db

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/solutions', methods=['GET'])
    def get_solutions():
        solutions = Solution.query.all()
        return jsonify([solution.to_dict() for solution in solutions]), 200

    @blueprint.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        return jsonify(solution.to_dict()), 200

    @blueprint.route('/solutions', methods=['POST'])
    def create_solution():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400

        try:
            new_solution = Solution(**data)
            db.session.add(new_solution)
            db.session.commit()
            return jsonify(new_solution.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/solutions/<int:solution_id>', methods=['PUT'])
    def update_solution(solution_id):
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400

        try:
            for key, value in data.items():
                setattr(solution, key, value)
            db.session.add(solution)
            db.session.commit()
            return jsonify(solution.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @blueprint.route('/solutions/<int:solution_id>', methods=['DELETE'])
    def delete_solution(solution_id):
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404

        try:
            db.session.delete(solution)
            db.session.commit()
            return jsonify({'message': 'Solution deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return blueprint