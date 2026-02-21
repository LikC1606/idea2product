from flask import Blueprint
from app.models.problem import Problem

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        # In a real application, you might fetch problems from the database
        problems = [
            {
                "id": 1,
                "title": "Two Sum",
                "difficulty": "Easy",
                "description": "Find two numbers that add up to a specific target."
            },
            {
                "id": 2,
                "title": "Longest Substring Without Repeating Characters",
                "difficulty": "Medium",
                "description": "Find the length of the longest substring without repeating characters."
            }
        ]
        return {"problems": problems}, 200

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        # Mock example of fetching a specific problem
        if problem_id == 1:
            problem = {
                "id": 1,
                "title": "Two Sum",
                "difficulty": "Easy",
                "description": "Find two numbers that add up to a specific target.",
                "examples": [
                    {"input": [2, 7, 11, 15], "target": 9, "output": [0, 1]}
                ]
            }
        elif problem_id == 2:
            problem = {
                "id": 2,
                "title": "Longest Substring Without Repeating Characters",
                "difficulty": "Medium",
                "description": "Find the length of the longest substring without repeating characters.",
                "examples": [
                    {"input": "abcabcbb", "output": 3}
                ]
            }
        else:
            return {"error": "Problem not found"}, 404

        return {"problem": problem}, 200

    return blueprint