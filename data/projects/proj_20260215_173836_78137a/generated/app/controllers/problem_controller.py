from flask import Blueprint
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        # Logic to fetch and return a list of problems
        problems = Problem.query.all()
        return {"problems": [problem.serialize() for problem in problems]}, 200

    @blueprint.route('/problem/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Logic to fetch and return a single problem by ID
        problem = Problem.query.get(problem_id)
        if problem is None:
            return {"error": "Problem not found"}, 404
        return {"problem": problem.serialize()}, 200

    return blueprint