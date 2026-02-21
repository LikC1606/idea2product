from flask import Blueprint
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

# Assembly layer: Registering blueprints for the application
def register_routes(app):
    app.register_blueprint(problem_bp, url_prefix='/problems')
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(solution_bp, url_prefix='/solutions')