from flask import Blueprint, request, jsonify
from app.models.tutorial import Tutorial
from app.database import db_session

hints_tutorials_bp = Blueprint('hints_tutorials', __name__)

@hints_tutorials_bp.route('/tutorials', methods=['GET'])
def get_tutorials():
    try:
        tutorials = Tutorial.query.all()
        tutorials_data = [tutorial.to_dict() for tutorial in tutorials]
        return jsonify({'status': 'success', 'data': tutorials_data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@hints_tutorials_bp.route('/tutorials/<int:tutorial_id>', methods=['GET'])
def get_tutorial(tutorial_id):
    try:
        tutorial = Tutorial.query.get(tutorial_id)
        if not tutorial:
            return jsonify({'status': 'error', 'message': 'Tutorial not found'}), 404
        return jsonify({'status': 'success', 'data': tutorial.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@hints_tutorials_bp.route('/tutorials', methods=['POST'])
def create_tutorial():
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        if not title or not content:
            return jsonify({'status': 'error', 'message': 'Missing title or content'}), 400

        tutorial = Tutorial(title=title, content=content)
        db_session.add(tutorial)
        db_session.commit()
        return jsonify({'status': 'success', 'data': tutorial.to_dict()}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@hints_tutorials_bp.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
def update_tutorial(tutorial_id):
    try:
        tutorial = Tutorial.query.get(tutorial_id)
        if not tutorial:
            return jsonify({'status': 'error', 'message': 'Tutorial not found'}), 404

        data = request.json
        title = data.get('title')
        content = data.get('content')

        if title:
            tutorial.title = title
        if content:
            tutorial.content = content

        db_session.commit()
        return jsonify({'status': 'success', 'data': tutorial.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@hints_tutorials_bp.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
def delete_tutorial(tutorial_id):
    try:
        tutorial = Tutorial.query.get(tutorial_id)
        if not tutorial:
            return jsonify({'status': 'error', 'message': 'Tutorial not found'}), 404

        db_session.delete(tutorial)
        db_session.commit()
        return jsonify({'status': 'success', 'message': 'Tutorial deleted successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500