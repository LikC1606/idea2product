from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.problem import Problem
from app.database import db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def list_problems():
    try:
        problems = Problem.query.all()
        return render_template('templates/problem.html', problems=problems)
    except Exception as e:
        flash(f"An error occurred while fetching problems: {str(e)}", 'danger')
        return redirect(url_for('index'))

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def view_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            flash('Problem not found.', 'warning')
            return redirect(url_for('problem.list_problems'))
        return render_template('templates/problem.html', problem=problem)
    except Exception as e:
        flash(f"An error occurred while fetching the problem: {str(e)}", 'danger')
        return redirect(url_for('problem.list_problems'))

@problem_bp.route('/problems/create', methods=['GET', 'POST'])
def create_problem():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')

        if not title or not description or not difficulty:
            flash('All fields are required.', 'warning')
            return redirect(url_for('problem.create_problem'))
        
        try:
            new_problem = Problem(title=title, description=description, difficulty=difficulty)
            db.session.add(new_problem)
            db.session.commit()
            flash('Problem created successfully!', 'success')
            return redirect(url_for('problem.list_problems'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while creating the problem: {str(e)}", 'danger')

    return render_template('templates/submit.html')

@problem_bp.route('/problems/<int:problem_id>/edit', methods=['GET', 'POST'])
def edit_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if not problem:
        flash('Problem not found.', 'warning')
        return redirect(url_for('problem.list_problems'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')

        if not title or not description or not difficulty:
            flash('All fields are required.', 'warning')
            return redirect(url_for('problem.edit_problem', problem_id=problem_id))
        
        try:
            problem.title = title
            problem.description = description
            problem.difficulty = difficulty
            db.session.commit()
            flash('Problem updated successfully!', 'success')
            return redirect(url_for('problem.list_problems'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating the problem: {str(e)}", 'danger')

    return render_template('templates/submit.html', problem=problem)

@problem_bp.route('/problems/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if not problem:
        flash('Problem not found.', 'warning')
        return redirect(url_for('problem.list_problems'))
    
    try:
        db.session.delete(problem)
        db.session.commit()
        flash('Problem deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the problem: {str(e)}", 'danger')
    
    return redirect(url_for('problem.list_problems'))