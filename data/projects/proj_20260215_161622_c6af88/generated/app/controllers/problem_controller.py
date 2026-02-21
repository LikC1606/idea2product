from flask import Blueprint, request, jsonify
from app.models.problem import Problem
from app.database import db

problem_controller_bp = Blueprint('problem_controller', __name__)

@problem_controller_bp.route('/problems', methods=['GET'])
def get_all_problems():
    try:
        problems = Problem.query.all()
        problems_data = [
            {
                "id": problem.id,
                "title": problem.title,
                "description": problem.description,
                "difficulty": problem.difficulty
            }
            for problem in problems
        ]
        return jsonify(problems_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@problem_controller_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem_by_id(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem:
            problem_data = {
                "id": problem.id,
                "title": problem.title,
                "description": problem.description,
                "difficulty": problem.difficulty
            }
            return jsonify(problem_data), 200
        else:
            return jsonify({"error": "Problem not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@problem_controller_bp.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.get_json()
        new_problem = Problem(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty')
        )
        db.session.add(new_problem)
        db.session.commit()
        return jsonify({"message": "Problem created successfully", "id": new_problem.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@problem_controller_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        data = request.get_json()
        problem = Problem.query.get(problem_id)
        if problem:
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            db.session.commit()
            return jsonify({"message": "Problem updated successfully"}), 200
        else:
            return jsonify({"error": "Problem not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@problem_controller_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem:
            db.session.delete(problem)
            db.session.commit()
            return jsonify({"message": "Problem deleted successfully"}), 200
        else:
            return jsonify({"error": "Problem not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def problem_controller():
    return problem_controller_bp