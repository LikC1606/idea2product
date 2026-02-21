from flask import Blueprint
from app.models.solution import Solution

def solution_blueprint():
    solution_bp = Blueprint('solution', __name__)

    @solution_bp.route('/solutions', methods=['GET'])
    def get_solutions():
        # This would typically return all solutions.
        # For now, it's a placeholder returning a generic response.
        return {"message": "List of solutions"}

    @solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
    def get_solution(solution_id):
        # This would typically fetch a solution by ID.
        # For now, it's a placeholder returning a generic response.
        return {"message": f"Details of solution {solution_id}"}

    return solution_bp