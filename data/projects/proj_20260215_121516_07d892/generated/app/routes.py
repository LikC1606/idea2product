from flask import Blueprint
from app.controllers.problem_library import problem_library_controller
from app.controllers.code_submission import code_submission_controller
from app.controllers.user_profile import user_profile_controller
from app.controllers.leaderboard import leaderboard_controller
from app.controllers.hints_tutorials import hints_tutorials_controller

routes = Blueprint('routes', __name__)

# Problem Library routes
@routes.route('/problems', methods=['GET'])
def get_problems():
    return problem_library_controller.get_all_problems()

@routes.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    return problem_library_controller.get_problem(problem_id)

# Code Submission routes
@routes.route('/submit', methods=['POST'])
def submit_code():
    return code_submission_controller.submit_code()

@routes.route('/submission/<int:submission_id>', methods=['GET'])
def get_submission(submission_id):
    return code_submission_controller.get_submission(submission_id)

# User Profile routes
@routes.route('/user/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    return user_profile_controller.get_user_profile(user_id)

@routes.route('/user/<int:user_id>', methods=['PUT'])
def update_user_profile(user_id):
    return user_profile_controller.update_user_profile(user_id)

# Leaderboard routes
@routes.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    return leaderboard_controller.get_leaderboard()

# Hints and Tutorials routes
@routes.route('/hints/<int:problem_id>', methods=['GET'])
def get_hints(problem_id):
    return hints_tutorials_controller.get_hints(problem_id)

@routes.route('/tutorials/<int:problem_id>', methods=['GET'])
def get_tutorials(problem_id):
    return hints_tutorials_controller.get_tutorials(problem_id)