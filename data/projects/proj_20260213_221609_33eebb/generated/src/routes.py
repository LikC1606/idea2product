from flask import Flask, request, jsonify
from src.controllers import task_controller

app = Flask(__name__)

@app.route('/tasks', methods=['POST'])
def create_task():
    try:
        task_data = request.json
        task = task_controller.create_task(task_data)
        return jsonify(task), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def edit_task(task_id):
    try:
        task_data = request.json
        task = task_controller.edit_task(task_id, task_data)
        return jsonify(task), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        task_controller.delete_task(task_id)
        return jsonify({'message': 'Task deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tasks/<int:task_id>/prioritize', methods=['PATCH'])
def prioritize_task(task_id):
    try:
        priority = request.json.get('priority')
        task = task_controller.prioritize_task(task_id, priority)
        return jsonify(task), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tasks/<int:task_id>/complete', methods=['PATCH'])
def complete_task(task_id):
    try:
        task = task_controller.complete_task(task_id)
        return jsonify(task), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)