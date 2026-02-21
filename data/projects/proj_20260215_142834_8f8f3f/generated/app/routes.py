from flask import Blueprint, request, jsonify
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.controllers.problem import get_problem_list, submit_code, get_problem_details
from app.controllers.user import get_user_profile, update_user_profile
from app.controllers.leaderboard import get_leaderboard

# Create a new SQLAlchemy session
Session = sessionmaker(bind=engine)
session = Session()

routes = Blueprint('routes', __name__)

@routes.route('/problems', methods=['GET'])
def problems():
    # Fetch and return the list of problems
    problems = get_problem_list(session)
    return jsonify(problems)

@routes.route('/problems/<int:problem_id>', methods=['GET'])
def problem_details(problem_id):
    # Fetch and return the details of a specific problem
    problem = get_problem_details(session, problem_id)
    return jsonify(problem)

@routes.route('/submit', methods=['POST'])
def submit():
    # Submit code for evaluation
    data = request.json
    result = submit_code(session, data['problem_id'], data['code'], data['user_id'])
    return jsonify(result)

@routes.route('/user/<int:user_id>', methods=['GET'])
def user_profile(user_id):
    # Fetch and return the user profile
    user_profile = get_user_profile(session, user_id)
    return jsonify(user_profile)

@routes.route('/user/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    # Update user profile
    data = request.json
    updated_profile = update_user_profile(session, user_id, data)
    return jsonify(updated_profile)

@routes.route('/leaderboard', methods=['GET'])
def leaderboard():
    # Fetch and return the leaderboard
    leaderboard_data = get_leaderboard(session)
    return jsonify(leaderboard_data)