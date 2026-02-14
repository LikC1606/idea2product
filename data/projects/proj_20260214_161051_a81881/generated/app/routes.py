from flask import Blueprint, request, jsonify
from app.controllers.task_controller import (
    get_all_tasks,
    create_task,
    update_task,
    delete_task,
    get_task_by_id
)

# Define the Blueprint for the routes
routes = Blueprint('routes', __name__)

@routes.route('/tasks', methods=['GET'])
def fetch_tasks():
    """Fetch all tasks."""
    tasks = get_all_tasks()
    return jsonify(tasks), 200

@routes.route('/tasks/<int:task_id>', methods=['GET'])
def fetch_task(task_id):
    """Fetch a specific task by ID."""
    task = get_task_by_id(task_id)
    if task:
        return jsonify(task), 200
    return jsonify({'error': 'Task not found'}), 404

@routes.route('/tasks', methods=['POST'])
def create_new_task():
    """Create a new task."""
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid or missing data'}), 400
    task = create_task(data)
    return jsonify(task), 201

@routes.route('/tasks/<int:task_id>', methods=['PUT'])
def modify_task(task_id):
    """Update an existing task."""
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid or missing data'}), 400
    updated_task = update_task(task_id, data)
    if updated_task:
        return jsonify(updated_task), 200
    return jsonify({'error': 'Task not found'}), 404

@routes.route('/tasks/<int:task_id>', methods=['DELETE'])
def remove_task(task_id):
    """Delete a task."""
    result = delete_task(task_id)
    if result:
        return jsonify({'message': 'Task deleted successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404