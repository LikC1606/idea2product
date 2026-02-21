from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.database import db
from app.models.problem import Problem
from app.models.solution import Solution
from app.models.user import User

assembly_bp = Blueprint('assembly', __name__)

@assembly_bp.route('/problems', methods=['GET'])
def list_problems():
    problems = Problem.query.all()
    return render_template('index.html', problems=problems)

@assembly_bp.route('/problems/<int:problem_id>', methods=['GET'])
def view_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if problem:
        return render_template('problem.html', problem=problem)
    return jsonify({'error': 'Problem not found'}), 404

@assembly_bp.route('/problems/create', methods=['GET', 'POST'])
def create_problem():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if title and description:
            problem = Problem(title=title, description=description)
            db.session.add(problem)
            db.session.commit()
            return redirect(url_for('assembly.list_problems'))
        return jsonify({'error': 'Invalid input'}), 400
    return render_template('submit.html')

@assembly_bp.route('/problems/<int:problem_id>/edit', methods=['GET', 'POST'])
def edit_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if not problem:
        return jsonify({'error': 'Problem not found'}), 404
    if request.method == 'POST':
        problem.title = request.form.get('title', problem.title)
        problem.description = request.form.get('description', problem.description)
        db.session.commit()
        return redirect(url_for('assembly.view_problem', problem_id=problem.id))
    return render_template('submit.html', problem=problem)

@assembly_bp.route('/problems/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if problem:
        db.session.delete(problem)
        db.session.commit()
        return redirect(url_for('assembly.list_problems'))
    return jsonify({'error': 'Problem not found'}), 404

@assembly_bp.route('/solutions', methods=['GET'])
def list_solutions():
    solutions = Solution.query.all()
    return jsonify([solution.to_dict() for solution in solutions])

@assembly_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if solution:
        return jsonify(solution.to_dict())
    return jsonify({'error': 'Solution not found'}), 404

@assembly_bp.route('/solutions/create', methods=['POST'])
def create_solution():
    user_id = request.json.get('user_id')
    problem_id = request.json.get('problem_id')
    code = request.json.get('code')
    if user_id and problem_id and code:
        solution = Solution(user_id=user_id, problem_id=problem_id, code=code)
        db.session.add(solution)
        db.session.commit()
        return jsonify(solution.to_dict()), 201
    return jsonify({'error': 'Invalid input'}), 400

@assembly_bp.route('/solutions/<int:solution_id>/edit', methods=['PUT'])
def edit_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404
    code = request.json.get('code')
    if code:
        solution.code = code
        db.session.commit()
        return jsonify(solution.to_dict())
    return jsonify({'error': 'Invalid input'}), 400

@assembly_bp.route('/solutions/<int:solution_id>/delete', methods=['DELETE'])
def delete_solution(solution_id):
    solution = Solution.query.get(solution_id)
    if solution:
        db.session.delete(solution)
        db.session.commit()
        return jsonify({'message': 'Solution deleted'})
    return jsonify({'error': 'Solution not found'}), 404