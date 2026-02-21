from flask import Blueprint, jsonify, request
from app.models.problem import Problem
from app.database import db

def problem_blueprint():
    blueprint = Blueprint('problem', __name__)

    @blueprint.route('/problems', methods=['GET'])
    def get_problems():
        try:
            problems = Problem.query.all()
            problems_data = [
                {
                    'id': problem.id,
                    'title': problem.title,
                    'description': problem.description,
                    'difficulty': problem.difficulty
                }
                for problem in problems
            ]
            return jsonify({'success': True, 'problems': problems_data}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['GET'])
    def get_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'success': False, 'error': 'Problem not found'}), 404
            
            problem_data = {
                'id': problem.id,
                'title': problem.title,
                'description': problem.description,
                'difficulty': problem.difficulty
            }
            return jsonify({'success': True, 'problem': problem_data}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @blueprint.route('/problems', methods=['POST'])
    def create_problem():
        try:
            data = request.json
            new_problem = Problem(
                title=data.get('title'),
                description=data.get('description'),
                difficulty=data.get('difficulty')
            )
            db.session.add(new_problem)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Problem created successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['PUT'])
    def update_problem(problem_id):
        try:
            data = request.json
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'success': False, 'error': 'Problem not found'}), 404
            
            problem.title = data.get('title', problem.title)
            problem.description = data.get('description', problem.description)
            problem.difficulty = data.get('difficulty', problem.difficulty)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Problem updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @blueprint.route('/problems/<int:problem_id>', methods=['DELETE'])
    def delete_problem(problem_id):
        try:
            problem = Problem.query.get(problem_id)
            if not problem:
                return jsonify({'success': False, 'error': 'Problem not found'}), 404
            
            db.session.delete(problem)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Problem deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    return blueprint