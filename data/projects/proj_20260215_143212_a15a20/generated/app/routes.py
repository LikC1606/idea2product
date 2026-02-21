from flask import Blueprint, request, jsonify
from app.controllers.problem_controller import (
    get_problems, get_problem_by_id, create_problem, update_problem, delete_problem
)
from app.controllers.user_controller import (
    get_users, get_user_by_id, create_user, update_user, delete_user
)
from app.controllers.solution_controller import (
    get_solutions, get_solution_by_id, submit_solution, update_solution, delete_solution
)
from app.controllers.leaderboard_controller import get_leaderboard
from app.controllers.discussion_controller import (
    get_discussions, get_discussion_by_id, create_discussion, update_discussion, delete_discussion
)

routes_bp = Blueprint('routes', __name__)

# Problem Routes
@routes_bp.route('/problems', methods=['GET'])
def problems():
    return jsonify(get_problems())

@routes_bp.route('/problems/<int:problem_id>', methods=['GET'])
def problem_detail(problem_id):
    return jsonify(get_problem_by_id(problem_id))

@routes_bp.route('/problems', methods=['POST'])
def problem_create():
    data = request.json
    return jsonify(create_problem(data))

@routes_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def problem_update(problem_id):
    data = request.json
    return jsonify(update_problem(problem_id, data))

@routes_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def problem_delete(problem_id):
    return jsonify(delete_problem(problem_id))

# User Routes
@routes_bp.route('/users', methods=['GET'])
def users():
    return jsonify(get_users())

@routes_bp.route('/users/<int:user_id>', methods=['GET'])
def user_detail(user_id):
    return jsonify(get_user_by_id(user_id))

@routes_bp.route('/users', methods=['POST'])
def user_create():
    data = request.json
    return jsonify(create_user(data))

@routes_bp.route('/users/<int:user_id>', methods=['PUT'])
def user_update(user_id):
    data = request.json
    return jsonify(update_user(user_id, data))

@routes_bp.route('/users/<int:user_id>', methods=['DELETE'])
def user_delete(user_id):
    return jsonify(delete_user(user_id))

# Solution Routes
@routes_bp.route('/solutions', methods=['GET'])
def solutions():
    return jsonify(get_solutions())

@routes_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def solution_detail(solution_id):
    return jsonify(get_solution_by_id(solution_id))

@routes_bp.route('/solutions', methods=['POST'])
def solution_submit():
    data = request.json
    return jsonify(submit_solution(data))

@routes_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
def solution_update(solution_id):
    data = request.json
    return jsonify(update_solution(solution_id, data))

@routes_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
def solution_delete(solution_id):
    return jsonify(delete_solution(solution_id))

# Leaderboard Route
@routes_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify(get_leaderboard())

# Discussion Routes
@routes_bp.route('/discussions', methods=['GET'])
def discussions():
    return jsonify(get_discussions())

@routes_bp.route('/discussions/<int:discussion_id>', methods=['GET'])
def discussion_detail(discussion_id):
    return jsonify(get_discussion_by_id(discussion_id))

@routes_bp.route('/discussions', methods=['POST'])
def discussion_create():
    data = request.json
    return jsonify(create_discussion(data))

@routes_bp.route('/discussions/<int:discussion_id>', methods=['PUT'])
def discussion_update(discussion_id):
    data = request.json
    return jsonify(update_discussion(discussion_id, data))

@routes_bp.route('/discussions/<int:discussion_id>', methods=['DELETE'])
def discussion_delete(discussion_id):
    return jsonify(delete_discussion(discussion_id))