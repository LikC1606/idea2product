from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db

problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = Problem.query.all()
        problem_list = [problem.to_dict() for problem in problems]
        return jsonify({"success": True, "problems": problem_list}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem_by_id(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"success": False, "message": "Problem not found"}), 404
        return jsonify({"success": True, "problem": problem.to_dict()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.get_json()
        new_problem = Problem(**data)
        db.session.add(new_problem)
        db.session.commit()
        return jsonify({"success": True, "problem": new_problem.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        data = request.get_json()
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"success": False, "message": "Problem not found"}), 404

        for key, value in data.items():
            setattr(problem, key, value)
        
        db.session.commit()
        return jsonify({"success": True, "problem": problem.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({"success": False, "message": "Problem not found"}), 404
        
        db.session.delete(problem)
        db.session.commit()
        return jsonify({"success": True, "message": "Problem deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500