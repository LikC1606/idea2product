from flask import Blueprint
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        # Placeholder for fetching and returning problems
        return {"message": "List of problems will be here"}

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Placeholder for fetching a specific problem
        return {"message": f"Problem {problem_id} details will be here"}

    return blueprint