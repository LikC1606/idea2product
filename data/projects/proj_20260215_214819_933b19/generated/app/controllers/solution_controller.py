from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.database import db
from app.models.solution import Solution
from app.models.problem import Problem

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def list_solutions():
    """Retrieve and list all solutions."""
    solutions = Solution.query.all()
    return jsonify([solution.to_dict() for solution in solutions])

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    """View a specific solution."""
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404
    return jsonify(solution.to_dict())

@solution_bp.route('/solutions/new', methods=['GET', 'POST'])
def create_solution():
    """Create a new solution."""
    if request.method == 'GET':
        problems = Problem.query.all()
        return render_template('submit.html', problems=problems)
    
    if request.method == 'POST':
        data = request.form
        problem_id = data.get('problem_id')
        content = data.get('content')
        
        if not problem_id or not content:
            return jsonify({'error': 'Problem ID and content are required'}), 400
        
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Invalid problem ID'}), 404
        
        solution = Solution(problem_id=problem_id, content=content)
        db.session.add(solution)
        db.session.commit()
        return redirect(url_for('solution.list_solutions'))

@solution_bp.route('/solutions/<int:solution_id>/edit', methods=['GET', 'POST'])
def edit_solution(solution_id):
    """Edit an existing solution."""
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404
    
    if request.method == 'GET':
        problems = Problem.query.all()
        return render_template('submit.html', solution=solution, problems=problems)
    
    if request.method == 'POST':
        data = request.form
        solution.content = data.get('content', solution.content)
        solution.problem_id = data.get('problem_id', solution.problem_id)
        
        db.session.commit()
        return redirect(url_for('solution.list_solutions'))

@solution_bp.route('/solutions/<int:solution_id>/delete', methods=['POST'])
def delete_solution(solution_id):
    """Delete a solution."""
    solution = Solution.query.get(solution_id)
    if not solution:
        return jsonify({'error': 'Solution not found'}), 404
    
    db.session.delete(solution)
    db.session.commit()
    return redirect(url_for('solution.list_solutions'))