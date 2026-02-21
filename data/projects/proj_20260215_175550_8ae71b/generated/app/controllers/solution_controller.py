from flask import Blueprint, request, jsonify
from app.models.solution import Solution

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/solutions', methods=['GET'])
    def get_solutions():
        try:
            solutions = Solution.query.all()
            response = [solution.to_dict() for solution in solutions]
            return jsonify(response), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions/<int:id>', methods=['GET'])
    def get_solution_by_id(id):
        try:
            solution = Solution.query.get(id)
            if solution:
                return jsonify(solution.to_dict()), 200
            else:
                return jsonify({'error': 'Solution not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions', methods=['POST'])
    def create_solution():
        try:
            data = request.get_json()
            new_solution = Solution(**data)
            db.session.add(new_solution)
            db.session.commit()
            return jsonify(new_solution.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions/<int:id>', methods=['PUT'])
    def update_solution(id):
        try:
            solution = Solution.query.get(id)
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

    @blueprint.route('/solutions/<int:id>', methods=['DELETE'])
    def delete_solution(id):
        try:
            solution = Solution.query.get(id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404

            db.session.delete(solution)
            db.session.commit()
            return jsonify({'message': 'Solution deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return blueprint