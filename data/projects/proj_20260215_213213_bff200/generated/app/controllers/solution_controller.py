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
    return jsonify([{
        'id': solution.id,
        'content': solution.content,
        'problem_id': solution.problem_id,
        'user_id': solution.user_id,
        'created_at': solution.created_at,
        'updated_at': solution.updated_at
    } for solution in solutions])

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def view_solution(solution_id):
    """View a single solution by ID."""
    solution = Solution.query.get_or_404(solution_id)
    return jsonify({
        'id': solution.id,
        'content': solution.content,
        'problem_id': solution.problem_id,
        'user_id': solution.user_id,
        'created_at': solution.created_at,
        'updated_at': solution.updated_at
    })

@solution_bp.route('/solutions/new', methods=['GET', 'POST'])
def create_solution():
    """Create a new solution."""
    if request.method == 'POST':
        data = request.json
        content = data.get('content')
        problem_id = data.get('problem_id')
        user_id = data.get('user_id')

        if not content or not problem_id or not user_id:
            return jsonify({'error': 'Missing fields'}), 400
        
        # Validate problem and user existence
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        new_solution = Solution(content=content, problem_id=problem_id, user_id=user_id)
        db.session.add(new_solution)
        db.session.commit()
        return jsonify({'message': 'Solution created successfully', 'id': new_solution.id}), 201
    
    return render_template('submit.html')

@solution_bp.route('/solutions/<int:solution_id>/edit', methods=['GET', 'POST'])
def edit_solution(solution_id):
    """Edit an existing solution."""
    solution = Solution.query.get_or_404(solution_id)

    if request.method == 'POST':
        data = request.json
        content = data.get('content')

        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        solution.content = content
        db.session.commit()
        return jsonify({'message': 'Solution updated successfully'})

    return render_template('submit.html', solution=solution)

@solution_bp.route('/solutions/<int:solution_id>/delete', methods=['POST'])
def delete_solution(solution_id):
    """Delete a solution."""
    solution = Solution.query.get_or_404(solution_id)
    db.session.delete(solution)
    db.session.commit()
    return jsonify({'message': 'Solution deleted successfully'})