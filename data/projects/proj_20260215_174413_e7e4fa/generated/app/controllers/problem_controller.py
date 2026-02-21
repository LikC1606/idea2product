from flask import Blueprint
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_all_problems():
        """
        Route to retrieve all problems.
        """
        # Simulating problem retrieval, assuming Problem.query.all() fetches all problems
        problems = Problem.query.all()
        problems_data = [{"id": problem.id, "title": problem.title, "description": problem.description} for problem in problems]
        return {"problems": problems_data}, 200

    @blueprint.route('/problem/<int:problem_id>', methods=['GET'])
    def get_problem_by_id(problem_id):
        """
        Route to retrieve a problem by its ID.
        """
        # Simulating problem retrieval, assuming Problem.query.get() fetches by ID
        problem = Problem.query.get(problem_id)
        if problem:
            return {"id": problem.id, "title": problem.title, "description": problem.description}, 200
        return {"error": "Problem not found"}, 404

    return blueprint