from flask import Blueprint, jsonify, request
from app.database import SessionLocal
from app.models.problem import Problem
from app.models.user import User
from app.models.solution import Solution

assembly_bp = Blueprint('assembly', __name__)

@assembly_bp.route('/assembly/problems', methods=['GET'])
def get_all_problems():
    """
    Retrieves all problems from the database.
    """
    session = SessionLocal()
    try:
        problems = session.query(Problem).all()
        return jsonify([problem.to_dict() for problem in problems]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@assembly_bp.route('/assembly/users', methods=['GET'])
def get_all_users():
    """
    Retrieves all users from the database.
    """
    session = SessionLocal()
    try:
        users = session.query(User).all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@assembly_bp.route('/assembly/solutions', methods=['GET'])
def get_all_solutions():
    """
    Retrieves all solutions from the database.
    """
    session = SessionLocal()
    try:
        solutions = session.query(Solution).all()
        return jsonify([solution.to_dict() for solution in solutions]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@assembly_bp.route('/assembly/solution', methods=['POST'])
def submit_solution():
    """
    Submits a new solution.
    """
    data = request.json
    session = SessionLocal()
    try:
        new_solution = Solution(
            code=data['code'],
            language=data['language'],
            status=data['status'],
            user_id=data['user_id'],
            problem_id=data['problem_id']
        )
        session.add(new_solution)
        session.commit()
        return jsonify({"message": "Solution submitted successfully", "solution_id": new_solution.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@assembly_bp.route('/assembly/problem', methods=['POST'])
def create_problem():
    """
    Creates a new problem.
    """
    data = request.json
    session = SessionLocal()
    try:
        new_problem = Problem(
            title=data['title'],
            description=data['description'],
            difficulty=data['difficulty']
        )
        session.add(new_problem)
        session.commit()
        return jsonify({"message": "Problem created successfully", "problem_id": new_problem.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@assembly_bp.route('/assembly/user', methods=['POST'])
def create_user():
    """
    Creates a new user.
    """
    data = request.json
    session = SessionLocal()
    try:
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        session.add(new_user)
        session.commit()
        return jsonify({"message": "User created successfully", "user_id": new_user.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()