from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import db
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def list_problems():
    """Fetch and display all problems."""
    problems = Problem.query.all()
    return render_template('problem.html', problems=problems)

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """Fetch and display a specific problem by ID."""
    problem = Problem.query.get_or_404(problem_id)
    return render_template('problem.html', problem=problem)

@problem_bp.route('/problems/new', methods=['GET', 'POST'])
def create_problem():
    """Create a new problem."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title or not description:
            flash('Title and Description are required!', 'error')
            return redirect(url_for('problem.create_problem'))

        new_problem = Problem(title=title, description=description)
        db.session.add(new_problem)
        db.session.commit()

        flash('Problem created successfully!', 'success')
        return redirect(url_for('problem.list_problems'))

    return render_template('submit.html')

@problem_bp.route('/problems/<int:problem_id>/edit', methods=['GET', 'POST'])
def edit_problem(problem_id):
    """Edit an existing problem."""
    problem = Problem.query.get_or_404(problem_id)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title or not description:
            flash('Title and Description are required!', 'error')
            return redirect(url_for('problem.edit_problem', problem_id=problem_id))

        problem.title = title
        problem.description = description
        db.session.commit()

        flash('Problem updated successfully!', 'success')
        return redirect(url_for('problem.list_problems'))

    return render_template('submit.html', problem=problem)

@problem_bp.route('/problems/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    """Delete a specific problem."""
    problem = Problem.query.get_or_404(problem_id)
    db.session.delete(problem)
    db.session.commit()

    flash('Problem deleted successfully!', 'success')
    return redirect(url_for('problem.list_problems'))