from flask import Blueprint, request, jsonify
from app.database import db
from app.models.problem import Problem

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['POST'])
def submit_solution():
    """
    Endpoint to submit a solution for a problem.
    Expects JSON payload with problem_id and solution_code.
    """
    data = request.get_json()
    problem_id = data.get('problem_id')
    solution_code = data.get('solution_code')

    if not problem_id or not solution_code:
        return jsonify({'error': 'problem_id and solution_code are required'}), 400

    # Fetch the problem from the database
    problem = Problem.query.filter_by(id=problem_id).first()

    if not problem:
        return jsonify({'error': 'Problem not found'}), 404

    # Evaluate the solution (dummy implementation for now)
    evaluation_result = evaluate_solution(problem, solution_code)

    return jsonify({'result': evaluation_result}), 200


def evaluate_solution(problem, solution_code):
    """
    Dummy solution evaluation function.
    Returns 'correct' if solution_code matches problem's expected solution.
    """
    # Assuming Problem model has an attribute `expected_solution`
    if solution_code.strip() == problem.expected_solution.strip():
        return 'correct'
    return 'incorrect'


@solution_bp.route('/solutions/<int:problem_id>', methods=['GET'])
def get_solutions_for_problem(problem_id):
    """
    Endpoint to fetch solutions for a specific problem.
    """
    problem = Problem.query.filter_by(id=problem_id).first()

    if not problem:
        return jsonify({'error': 'Problem not found'}), 404

    # Assuming Problem model has a relationship `solutions` to fetch solutions
    solutions = [
        {'id': solution.id, 'solution_code': solution.solution_code}
        for solution in problem.solutions
    ]

    return jsonify({'solutions': solutions}), 200