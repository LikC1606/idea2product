from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import db
from app.models.problem import Problem

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def list_problems():
    # Fetch all problems from the database
    problems = Problem.query.all()
    return render_template('problem.html', problems=problems)

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def view_problem(problem_id):
    # Fetch a specific problem by ID
    problem = Problem.query.get_or_404(problem_id)
    return render_template('submit.html', problem=problem)

@problem_bp.route('/problems/new', methods=['GET', 'POST'])
def create_problem():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')

        if not title or not description or not difficulty:
            flash('All fields are required!', 'error')
            return redirect(url_for('problem.create_problem'))
        
        # Create and save new problem
        new_problem = Problem(title=title, description=description, difficulty=difficulty)
        db.session.add(new_problem)
        db.session.commit()
        flash('Problem created successfully!', 'success')
        return redirect(url_for('problem.list_problems'))

    return render_template('index.html')

@problem_bp.route('/problems/<int:problem_id>/edit', methods=['GET', 'POST'])
def edit_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)

    if request.method == 'POST':
        problem.title = request.form.get('title')
        problem.description = request.form.get('description')
        problem.difficulty = request.form.get('difficulty')

        if not problem.title or not problem.description or not problem.difficulty:
            flash('All fields are required!', 'error')
            return redirect(url_for('problem.edit_problem', problem_id=problem_id))

        # Update and save problem
        db.session.commit()
        flash('Problem updated successfully!', 'success')
        return redirect(url_for('problem.view_problem', problem_id=problem_id))

    return render_template('index.html', problem=problem)

@problem_bp.route('/problems/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)

    # Delete the problem
    db.session.delete(problem)
    db.session.commit()
    flash('Problem deleted successfully!', 'success')
    return redirect(url_for('problem.list_problems'))