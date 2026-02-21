from flask import Blueprint
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

# Blueprint for assembly layer routes
assembly_bp = Blueprint('assembly', __name__)

# Register individual blueprints for problem, user, and solution routes
def register_routes(app):
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)
    app.register_blueprint(assembly_bp)