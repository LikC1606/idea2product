from flask import Blueprint
from app.models.problem import Problem

def problem_blueprint():
    problem_bp = Blueprint('problem', __name__)

    @problem_bp.route('/problems', methods=['GET'])
    def get_problems():
        # Here we would typically retrieve problems from the database
        # Since no database is specified, we'll return a placeholder response
        problems = [
            {"id": 1, "title": "Two Sum", "difficulty": "Easy"},
            {"id": 2, "title": "Longest Substring Without Repeating Characters", "difficulty": "Medium"},
            {"id": 3, "title": "Median of Two Sorted Arrays", "difficulty": "Hard"}
        ]
        return {"problems": problems}, 200

    @problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Placeholder logic for retrieving a specific problem
        problem = {"id": problem_id, "title": "Example Problem", "difficulty": "Medium"}
        return {"problem": problem}, 200

    return problem_bp