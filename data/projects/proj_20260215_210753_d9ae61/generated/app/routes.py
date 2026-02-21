from flask import Blueprint, render_template, redirect, url_for
from app.database import db
from app.models.problem import Problem
from app.models.user import User
from app.models.solution import Solution
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

# Create a blueprint for assembly-level routes
assembly_bp = Blueprint('assembly', __name__)

# Register the blueprints for other layers
def register_routes(app):
    app.register_blueprint(problem_bp, url_prefix='/problems')
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(solution_bp, url_prefix='/solutions')
    app.register_blueprint(assembly_bp)  # Register this blueprint if needed for future routes

# Example route for assembly layer (can be extended as needed)
@assembly_bp.route('/dashboard')
def dashboard():
    # Example: Display counts of problems, users, and solutions
    problem_count = db.session.query(Problem).count()
    user_count = db.session.query(User).count()
    solution_count = db.session.query(Solution).count()
    return render_template('dashboard.html', problem_count=problem_count, 
                           user_count=user_count, solution_count=solution_count)