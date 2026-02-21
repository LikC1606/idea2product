# app/routes/problem_routes.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database import db
from app.models.problem import Problem

# Must Export
problem_bp = Blueprint('problem', __name__)

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    try:
        problems = Problem.query.all()
        result = [problem.to_dict() for problem in problems]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem is None:
            return jsonify({"error": "Problem not found"}), 404
        return jsonify(problem.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@problem_bp.route('/problems', methods=['POST'])
def create_problem():
    try:
        data = request.get_json()
        new_problem = Problem(
            title=data['title'],
            description=data['description'],
            difficulty=data['difficulty']
        )
        db.session.add(new_problem)
        db.session.commit()
        return jsonify(new_problem.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    except KeyError:
        return jsonify({"error": "Missing required fields"}), 400

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    try:
        data = request.get_json()
        problem = Problem.query.get(problem_id)
        if problem is None:
            return jsonify({"error": "Problem not found"}), 404
        
        problem.title = data.get('title', problem.title)
        problem.description = data.get('description', problem.description)
        problem.difficulty = data.get('difficulty', problem.difficulty)
        
        db.session.commit()
        return jsonify(problem.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    try:
        problem = Problem.query.get(problem_id)
        if problem is None:
            return jsonify({"error": "Problem not found"}), 404
        
        db.session.delete(problem)
        db.session.commit()
        return jsonify({"message": "Problem deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500