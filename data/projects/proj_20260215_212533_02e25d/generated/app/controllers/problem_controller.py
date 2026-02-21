from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.problem import Problem
from app.database import db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def list_problems():
    try:
        problems = Problem.query.all()
        return render_template('problem.html', problems=problems)
    except Exception as e:
        flash(f"Error loading problems: {str(e)}", "danger")
        return redirect(url_for('index'))

@problem_bp.route('/problem/<int:problem_id>', methods=['GET'])
def view_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            flash("Problem not found", "danger")
            return redirect(url_for('list_problems'))
        return render_template('problem.html', problem=problem)
    except Exception as e:
        flash(f"Error loading problem: {str(e)}", "danger")
        return redirect(url_for('list_problems'))

@problem_bp.route('/problem/new', methods=['GET', 'POST'])
def create_problem():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')
        try:
            new_problem = Problem(title=title, description=description, difficulty=difficulty)
            db.session.add(new_problem)
            db.session.commit()
            flash("Problem created successfully", "success")
            return redirect(url_for('list_problems'))
        except Exception as e:
            flash(f"Error creating problem: {str(e)}", "danger")
            return redirect(url_for('create_problem'))
    return render_template('submit.html')

@problem_bp.route('/problem/<int:problem_id>/edit', methods=['GET', 'POST'])
def edit_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if not problem:
        flash("Problem not found", "danger")
        return redirect(url_for('list_problems'))
    if request.method == 'POST':
        problem.title = request.form.get('title')
        problem.description = request.form.get('description')
        problem.difficulty = request.form.get('difficulty')
        try:
            db.session.commit()
            flash("Problem updated successfully", "success")
            return redirect(url_for('view_problem', problem_id=problem.id))
        except Exception as e:
            flash(f"Error updating problem: {str(e)}", "danger")
            return redirect(url_for('edit_problem', problem_id=problem.id))
    return render_template('submit.html', problem=problem)

@problem_bp.route('/problem/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    problem = Problem.query.get(problem_id)
    if not problem:
        flash("Problem not found", "danger")
        return redirect(url_for('list_problems'))
    try:
        db.session.delete(problem)
        db.session.commit()
        flash("Problem deleted successfully", "success")
        return redirect(url_for('list_problems'))
    except Exception as e:
        flash(f"Error deleting problem: {str(e)}", "danger")
        return redirect(url_for('list_problems'))