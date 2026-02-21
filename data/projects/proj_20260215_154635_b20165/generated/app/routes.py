from flask import Blueprint
from app.controllers.problem_controller import problem_blueprint
from app.controllers.user_controller import user_blueprint
from app.controllers.solution_controller import solution_blueprint

# Main Blueprint for aggregating all the blueprints
main_blueprint = Blueprint('main', __name__)

# Registering all blueprints
main_blueprint.register_blueprint(problem_blueprint, url_prefix='/problems')
main_blueprint.register_blueprint(user_blueprint, url_prefix='/users')
main_blueprint.register_blueprint(solution_blueprint, url_prefix='/solutions')