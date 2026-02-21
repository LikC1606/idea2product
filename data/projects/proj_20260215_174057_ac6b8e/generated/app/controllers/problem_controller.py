from flask import Blueprint
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def list_problems():
        """
        List all problems.
        """
        problems = Problem.query.all()
        return {'problems': [problem.to_dict() for problem in problems]}

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        """
        Retrieve a specific problem by ID.
        """
        problem = Problem.query.get_or_404(problem_id)
        return problem.to_dict()

    return blueprint