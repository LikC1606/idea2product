from flask import Blueprint, request, jsonify
from app.models import Task, db
from datetime import datetime

task_controller = Blueprint('task_controller', __name__)

@task_controller.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

@task_controller.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return jsonify(task.to_dict())
    return jsonify({'error': 'Task not found'}), 404

@task_controller.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    priority = data.get('priority', 'Normal')
    due_date = data.get('due_date')
    if due_date:
        due_date = datetime.strptime(due_date, '%Y-%m-%d')
    
    new_task = Task(title=title, description=description, priority=priority, due_date=due_date)
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify(new_task.to_dict()), 201

@task_controller.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.json
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.priority = data.get('priority', task.priority)
    due_date = data.get('due_date', task.due_date)
    if due_date:
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
    
    db.session.commit()
    return jsonify(task.to_dict())

@task_controller.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})

@task_controller.route('/tasks/notifications', methods=['GET'])
def get_notifications():
    tasks = Task.query.filter(Task.due_date <= datetime.now()).all()
    notifications = [{'task_id': task.id, 'title': task.title, 'due_date': task.due_date} for task in tasks]
    return jsonify(notifications)