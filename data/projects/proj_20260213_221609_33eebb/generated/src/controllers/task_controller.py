from flask import Blueprint, request, jsonify
from src.models.task_model import Task

task_controller = Blueprint('task_controller', __name__)

# Create a new task
@task_controller.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    task = Task(name=data['name'], description=data.get('description', ''), priority=data.get('priority', 'Low'))
    task.save()
    return jsonify({'message': 'Task created successfully', 'task': task.to_dict()}), 201

# Get all tasks
@task_controller.route('/tasks', methods=['GET'])
def get_all_tasks():
    tasks = Task.get_all()
    return jsonify({'tasks': [task.to_dict() for task in tasks]}), 200

# Get a specific task by ID
@task_controller.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    return jsonify({'task': task.to_dict()}), 200

# Edit a task
@task_controller.route('/tasks/<int:task_id>', methods=['PUT'])
def edit_task(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    data = request.get_json()
    task.name = data.get('name', task.name)
    task.description = data.get('description', task.description)
    task.priority = data.get('priority', task.priority)
    task.completed = data.get('completed', task.completed)
    task.save()
    return jsonify({'message': 'Task updated successfully', 'task': task.to_dict()}), 200

# Delete a task
@task_controller.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    task.delete()
    return jsonify({'message': 'Task deleted successfully'}), 200

# Mark task as complete
@task_controller.route('/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    task.completed = True
    task.save()
    return jsonify({'message': 'Task marked as complete', 'task': task.to_dict()}), 200

# Change task priority
@task_controller.route('/tasks/<int:task_id>/priority', methods=['PUT'])
def change_priority(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    data = request.get_json()
    task.priority = data.get('priority', task.priority)
    task.save()
    return jsonify({'message': 'Task priority updated', 'task': task.to_dict()}), 200
```
