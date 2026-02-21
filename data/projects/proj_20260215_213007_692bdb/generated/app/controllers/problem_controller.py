from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import db
from app.models.problem import Problem
from app.models.solution import Solution

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def list_problems():
    """Route to list all problems"""
    problems = Problem.query.all()
    return render_template('templates/problem.html', problems=problems)

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def view_problem(problem_id):
    """Route to view a problem by its ID"""
    problem = Problem.query.get_or_404(problem_id)
    solutions = Solution.query.filter_by(problem_id=problem_id).all()
    return render_template('templates/submit.html', problem=problem, solutions=solutions)

@problem_bp.route('/problems/new', methods=['GET', 'POST'])
def create_problem():
    """Route to create a new problem"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title or not description:
            flash('Title and description are required.', 'error')
            return redirect(request.url)

        new_problem = Problem(title=title, description=description)
        db.session.add(new_problem)
        db.session.commit()

        flash('Problem created successfully!', 'success')
        return redirect(url_for('problem.list_problems'))

    return render_template('templates/index.html')

@problem_bp.route('/problems/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    """Route to delete a problem by its ID"""
    problem = Problem.query.get_or_404(problem_id)
    db.session.delete(problem)
    db.session.commit()

    flash('Problem deleted successfully!', 'success')
    return redirect(url_for('problem.list_problems'))