from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from app.models.problem import Problem, Hint
from app import db

hints_blueprint = Blueprint('hints', __name__)

@hints_blueprint.route('/hints/<int:problem_id>', methods=['GET'])
def get_hints(problem_id):
    session: Session = db.session
    try:
        problem = session.query(Problem).filter_by(id=problem_id).first()
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404
        
        hints = session.query(Hint).filter_by(problem_id=problem_id).all()
        hints_data = [{'id': hint.id, 'text': hint.text} for hint in hints]

        return jsonify({'hints': hints_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hints_blueprint.route('/hints/<int:problem_id>', methods=['POST'])
def add_hint(problem_id):
    session: Session = db.session
    try:
        problem = session.query(Problem).filter_by(id=problem_id).first()
        if not problem:
            return jsonify({'error': 'Problem not found'}), 404

        hint_text = request.json.get('text')
        if not hint_text:
            return jsonify({'error': 'Hint text is required'}), 400

        new_hint = Hint(problem_id=problem_id, text=hint_text)
        session.add(new_hint)
        session.commit()

        return jsonify({'message': 'Hint added successfully', 'hint_id': new_hint.id}), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

@hints_blueprint.route('/hints/<int:hint_id>', methods=['PUT'])
def update_hint(hint_id):
    session: Session = db.session
    try:
        hint = session.query(Hint).filter_by(id=hint_id).first()
        if not hint:
            return jsonify({'error': 'Hint not found'}), 404

        hint_text = request.json.get('text')
        if not hint_text:
            return jsonify({'error': 'Hint text is required'}), 400

        hint.text = hint_text
        session.commit()

        return jsonify({'message': 'Hint updated successfully'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

@hints_blueprint.route('/hints/<int:hint_id>', methods=['DELETE'])
def delete_hint(hint_id):
    session: Session = db.session
    try:
        hint = session.query(Hint).filter_by(id=hint_id).first()
        if not hint:
            return jsonify({'error': 'Hint not found'}), 404

        session.delete(hint)
        session.commit()

        return jsonify({'message': 'Hint deleted successfully'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500