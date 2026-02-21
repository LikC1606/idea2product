from flask import Blueprint, render_template
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

def register_routes(app):
    """
    Register all routes and blueprints for the application.
    This ensures that all controllers are properly linked to the Flask app.
    """
    # Register blueprints from controllers
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)

    # Additional route definitions can go here
    @app.route('/')
    def home():
        return render_template('index.html')