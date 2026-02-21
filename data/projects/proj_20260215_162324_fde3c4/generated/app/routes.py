# app/routes.py
from flask import Blueprint
from app.controllers.problem_controller import problem_controller
from app.controllers.user_controller import user_controller
from app.controllers.solution_controller import solution_controller

def register_blueprints(app):
    app.register_blueprint(problem_controller, url_prefix="/problems")
    app.register_blueprint(user_controller, url_prefix="/users")
    app.register_blueprint(solution_controller, url_prefix="/solutions")