from flask import Flask, jsonify, request
from sqlalchemy.orm import scoped_session
from app import db_session, init_app
from app.models.problem import get_problem
from app.models.user import get_user
from app.models.leaderboard import get_leaderboard

# Initialize Flask app
app = Flask(__name__)
init_app(app)

@app.route('/')
def index():
    return "Welcome to the ACM Problem-Solving Platform!"

@app.route('/problems/<int:problem_id>', methods=['GET'])
def fetch_problem(problem_id):
    try:
        problem = get_problem(db_session, problem_id)
        if problem:
            return jsonify(problem.to_dict()), 200
        return jsonify({"error": "Problem not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def fetch_user(user_id):
    try:
        user = get_user(db_session, user_id)
        if user:
            return jsonify(user.to_dict()), 200
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/leaderboard', methods=['GET'])
def fetch_leaderboard():
    try:
        leaderboard = get_leaderboard(db_session)
        if leaderboard:
            return jsonify([entry.to_dict() for entry in leaderboard]), 200
        return jsonify({"error": "Leaderboard is empty"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)