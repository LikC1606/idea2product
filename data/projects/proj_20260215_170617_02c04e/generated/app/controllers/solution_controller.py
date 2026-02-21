from flask import Blueprint, jsonify, request
from app.models.solution import Solution

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/solutions', methods=['GET'])
    def get_all_solutions():
        try:
            solutions = Solution.query.all()
            solutions_data = [solution.to_dict() for solution in solutions]
            return jsonify({'solutions': solutions_data}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404
            return jsonify({'solution': solution.to_dict()}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions', methods=['POST'])
    def create_solution():
        try:
            data = request.get_json()
            new_solution = Solution(**data)
            db.session.add(new_solution)
            db.session.commit()
            return jsonify({'message': 'Solution created', 'solution': new_solution.to_dict()}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions/<int:solution_id>', methods=['PUT'])
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
            return jsonify({'message': 'Solution updated', 'solution': solution.to_dict()}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @blueprint.route('/solutions/<int:solution_id>', methods=['DELETE'])
    def delete_solution(solution_id):
        try:
            solution = Solution.query.get(solution_id)
            if not solution:
                return jsonify({'error': 'Solution not found'}), 404
            
            db.session.delete(solution)
            db.session.commit()
            return jsonify({'message': 'Solution deleted'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return blueprint