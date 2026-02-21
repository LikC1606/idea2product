from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.models.problem import Problem
from app.models.solution import Solution
from app.models.user import User
from app.database import db

assembly_bp = Blueprint('assembly', __name__)

@assembly_bp.route('/problems', methods=['GET'])
def list_problems():
    problems = Problem.query.all()
    return render_template('index.html', problems=problems)

@assembly_bp.route('/problems/<int:problem_id>', methods=['GET'])
def view_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    solutions = Solution.query.filter_by(problem_id=problem_id).all()
    return render_template('problem.html', problem=problem, solutions=solutions)

@assembly_bp.route('/problems/new', methods=['GET', 'POST'])
def create_problem():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if not title or not description:
            flash('Please fill in all the fields.', 'error')
            return redirect(url_for('assembly.create_problem'))
        
        new_problem = Problem(title=title, description=description)
        db.session.add(new_problem)
        db.session.commit()
        flash('Problem created successfully!', 'success')
        return redirect(url_for('assembly.list_problems'))
    return render_template('submit.html')

@assembly_bp.route('/problems/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    db.session.delete(problem)
    db.session.commit()
    flash('Problem deleted successfully!', 'success')
    return redirect(url_for('assembly.list_problems'))

@assembly_bp.route('/solutions/new', methods=['POST'])
def create_solution():
    problem_id = request.form.get('problem_id')
    user_id = request.form.get('user_id')
    content = request.form.get('content')
    
    if not problem_id or not user_id or not content:
        flash('All fields are required.', 'error')
        return redirect(request.referrer)
    
    new_solution = Solution(problem_id=problem_id, user_id=user_id, content=content)
    db.session.add(new_solution)
    db.session.commit()
    flash('Solution submitted successfully!', 'success')
    return redirect(url_for('assembly.view_problem', problem_id=problem_id))

@assembly_bp.route('/solutions/<int:solution_id>/delete', methods=['POST'])
def delete_solution(solution_id):
    solution = Solution.query.get_or_404(solution_id)
    problem_id = solution.problem_id
    db.session.delete(solution)
    db.session.commit()
    flash('Solution deleted successfully!', 'success')
    return redirect(url_for('assembly.view_problem', problem_id=problem_id))