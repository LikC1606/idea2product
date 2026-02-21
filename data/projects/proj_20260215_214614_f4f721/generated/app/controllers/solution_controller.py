from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.database import db
from app.models.solution import Solution
from app.models.problem import Problem
from app.models.user import User

solution_bp = Blueprint('solution', __name__)

@solution_bp.route('/solutions', methods=['GET'])
def list_solutions():
    """List all solutions."""
    solutions = Solution.query.all()
    return render_template('solutions/index.html', solutions=solutions)

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution(solution_id):
    """Get a specific solution by ID."""
    solution = Solution.query.get_or_404(solution_id)
    return render_template('solutions/show.html', solution=solution)

@solution_bp.route('/solutions/new', methods=['GET', 'POST'])
def create_solution():
    """Create a new solution."""
    if request.method == 'POST':
        content = request.form['content']
        problem_id = request.form['problem_id']
        user_id = request.form['user_id']

        # Validate problem and user existence
        problem = Problem.query.get(problem_id)
        user = User.query.get(user_id)
        if not problem or not user:
            return jsonify({'error': 'Invalid problem or user ID'}), 400

        solution = Solution(content=content, problem_id=problem_id, user_id=user_id)
        db.session.add(solution)
        db.session.commit()
        return redirect(url_for('solution.list_solutions'))

    problems = Problem.query.all()
    users = User.query.all()
    return render_template('solutions/new.html', problems=problems, users=users)

@solution_bp.route('/solutions/<int:solution_id>/edit', methods=['GET', 'POST'])
def edit_solution(solution_id):
    """Edit an existing solution."""
    solution = Solution.query.get_or_404(solution_id)

    if request.method == 'POST':
        solution.content = request.form['content']
        db.session.commit()
        return redirect(url_for('solution.get_solution', solution_id=solution.id))

    return render_template('solutions/edit.html', solution=solution)

@solution_bp.route('/solutions/<int:solution_id>/delete', methods=['POST'])
def delete_solution(solution_id):
    """Delete a solution by ID."""
    solution = Solution.query.get_or_404(solution_id)
    db.session.delete(solution)
    db.session.commit()
    return redirect(url_for('solution.list_solutions'))