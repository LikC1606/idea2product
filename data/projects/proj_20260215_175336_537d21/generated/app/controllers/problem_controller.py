from flask import Blueprint
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__, url_prefix='/problem')

    @blueprint.route('/', methods=['GET'])
    def get_problems():
        # Logic to fetch and return list of problems (dummy example)
        problems = Problem.query.all()
        return {"problems": [problem.to_dict() for problem in problems]}

    @blueprint.route('/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Logic to fetch and return a single problem by ID (dummy example)
        problem = Problem.query.get(problem_id)
        if not problem:
            return {"error": "Problem not found"}, 404
        return problem.to_dict()

    return blueprint