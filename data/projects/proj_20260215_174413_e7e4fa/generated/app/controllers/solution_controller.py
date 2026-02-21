from flask import Blueprint
from app.models.solution import Solution

def solution_blueprint():
    blueprint = Blueprint('solution', __name__)

    @blueprint.route('/solutions', methods=['GET'])
    def list_solutions():
        # Example function, replace with actual functionality
        solutions = Solution.query.all()
        return {'solutions': [solution.to_dict() for solution in solutions]}, 200

    @blueprint.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        # Example function, replace with actual functionality
        solution = Solution.query.get(solution_id)
        if not solution:
            return {'error': 'Solution not found'}, 404
        return solution.to_dict(), 200

    return blueprint