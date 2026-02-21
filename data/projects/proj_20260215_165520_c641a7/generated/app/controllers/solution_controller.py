from flask import Blueprint, jsonify, request
from app.models.solution import Solution

def solution_blueprint():
    solution_bp = Blueprint('solutions', __name__)

    @solution_bp.route('/solutions', methods=['GET'])
    def get_solutions():
        """Retrieve all solutions."""
        solutions = Solution.query.all()
        solutions_data = [solution.as_dict() for solution in solutions]
        return jsonify(solutions_data), 200

    @solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        """Retrieve a solution by its ID."""
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        return jsonify(solution.as_dict()), 200

    @solution_bp.route('/solutions', methods=['POST'])
    def create_solution():
        """Create a new solution."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        try:
            new_solution = Solution(**data)
            new_solution.save()
            return jsonify(new_solution.as_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
    def update_solution(solution_id):
        """Update an existing solution."""
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input'}), 400
        try:
            for key, value in data.items():
                setattr(solution, key, value)
            solution.save()
            return jsonify(solution.as_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
    def delete_solution(solution_id):
        """Delete a solution by its ID."""
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Solution not found'}), 404
        try:
            solution.delete()
            return jsonify({'message': 'Solution deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return solution_bp