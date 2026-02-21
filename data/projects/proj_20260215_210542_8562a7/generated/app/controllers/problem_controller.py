from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import db
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__, url_prefix='/problems')

@problem_bp.route('/')
def list_problems():
    """List all problems."""
    problems = Problem.query.all()
    return render_template('templates/problem.html', problems=problems)

@problem_bp.route('/<int:problem_id>')
def view_problem(problem_id):
    """View details of a specific problem."""
    problem = Problem.query.get(problem_id)
    if not problem:
        flash('Problem not found.', 'error')
        return redirect(url_for('problem.list_problems'))
    return render_template('templates/problem.html', problem=problem)

@problem_bp.route('/create', methods=['GET', 'POST'])
def create_problem():
    """Create a new problem."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')

        if not title or not description or not difficulty:
            flash('All fields are required.', 'error')
            return redirect(url_for('problem.create_problem'))

        new_problem = Problem(title=title, description=description, difficulty=difficulty)
        db.session.add(new_problem)
        db.session.commit()
        flash('Problem created successfully.', 'success')
        return redirect(url_for('problem.list_problems'))

    return render_template('templates/submit.html')

@problem_bp.route('/<int:problem_id>/edit', methods=['GET', 'POST'])
def edit_problem(problem_id):
    """Edit an existing problem."""
    problem = Problem.query.get(problem_id)
    if not problem:
        flash('Problem not found.', 'error')
        return redirect(url_for('problem.list_problems'))

    if request.method == 'POST':
        problem.title = request.form.get('title')
        problem.description = request.form.get('description')
        problem.difficulty = request.form.get('difficulty')

        if not problem.title or not problem.description or not problem.difficulty:
            flash('All fields are required.', 'error')
            return redirect(url_for('problem.edit_problem', problem_id=problem_id))

        db.session.commit()
        flash('Problem updated successfully.', 'success')
        return redirect(url_for('problem.view_problem', problem_id=problem_id))

    return render_template('templates/submit.html', problem=problem)

@problem_bp.route('/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    """Delete an existing problem."""
    problem = Problem.query.get(problem_id)
    if not problem:
        flash('Problem not found.', 'error')
        return redirect(url_for('problem.list_problems'))

    db.session.delete(problem)
    db.session.commit()
    flash('Problem deleted successfully.', 'success')
    return redirect(url_for('problem.list_problems'))