"""Project API Blueprint."""

import os
import json
from flask import Blueprint, jsonify, request
from flask_socketio import emit

from src.web.services.task_service import task_service
from config.settings import Settings
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.services.llm_service import LLMService

bp = Blueprint('projects', __name__, url_prefix='/api/projects')


@bp.route('/analyze', methods=['POST'])
def analyze_requirement():
    """
    Analyze a requirement and generate clarification questions.

    Request body:
    {
        "requirement": "Build a todo app"
    }

    Returns:
    {
        "needs_clarification": true/false,
        "questions": [{"question": "...", "reason": "..."}],
        "improvements": [...]
    }
    """
    data = request.get_json()
    requirement = data.get('requirement', '')

    if not requirement:
        return jsonify({'error': 'requirement is required'}), 400

    try:
        settings = Settings()
        llm_service = LLMService(settings)
        agent = InteractionAgent(llm_service)

        analysis = agent.analyze_requirement(requirement)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/clarify', methods=['POST'])
def clarify_requirement():
    """
    Generate clarification questions for a requirement.

    Request body:
    {
        "requirement": "Build a todo app"
    }

    Returns:
    {
        "questions": [{"id": "q1", "category": "...", "question": "..."}]
    }
    """
    data = request.get_json()
    requirement = data.get('requirement', '')

    if not requirement:
        return jsonify({'error': 'requirement is required'}), 400

    try:
        settings = Settings()
        llm_service = LLMService(settings)
        agent = InteractionAgent(llm_service)

        questions = agent.generate_clarification_questions(requirement)
        return jsonify({
            'questions': [
                {'id': q.id, 'category': q.category, 'question': q.question}
                for q in questions
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/finalize', methods=['POST'])
def finalize_requirement():
    """
    Generate final requirements from initial requirement + clarifications.

    Request body:
    {
        "requirement": "Build a todo app",
        "clarifications": {"question1": "answer1", "question2": "answer2"}
    }

    Returns:
    {
        "title": "...",
        "description": "...",
        "features": [...],
        ...
    }
    """
    data = request.get_json()
    requirement = data.get('requirement', '')
    clarifications = data.get('clarifications', {})

    if not requirement:
        return jsonify({'error': 'requirement is required'}), 400

    try:
        settings = Settings()
        llm_service = LLMService(settings)
        agent = InteractionAgent(llm_service)

        # Create dummy questions list from clarifications
        questions = [
            type('Question', (), {'id': f'q{i}', 'question': q})()
            for i, q in enumerate(clarifications.keys(), 1)
        ]

        final_req = agent._generate_final_requirements(requirement, questions, clarifications)

        return jsonify({
            'title': final_req.title,
            'description': final_req.description,
            'features': [
                {'id': f.id, 'name': f.name, 'description': f.description, 'priority': f.priority}
                for f in final_req.features
            ],
            'constraints': final_req.constraints,
            'target_users': final_req.target_users,
            'data_requirements': final_req.data_requirements
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
def create_project():
    """
    Create a new project.

    Request body:
    {
        "requirement": "Build a todo app",
        "interactive": false  // Optional: enable interactive Q&A mode
    }

    Returns:
    {
        "project_id": "proj_xxx",
        "status": "pending"
    }
    """
    data = request.get_json()
    requirement = data.get('requirement', '')
    interactive = data.get('interactive', False)
    clarifications = data.get('clarifications', {})

    if not requirement:
        return jsonify({'error': 'requirement is required'}), 400

    # Create project through task service
    project_id = task_service.create_project(requirement, interactive=interactive, clarifications=clarifications)

    return jsonify({
        'project_id': project_id,
        'status': 'pending',
        'message': 'Project created, processing started'
    }), 201


@bp.route('', methods=['GET'])
def list_projects():
    """
    List all projects.

    Returns:
    {
        "projects": [
            {
                "project_id": "proj_xxx",
                "requirement": "Build a todo app",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00"
            }
        ]
    }
    """
    projects = task_service.list_projects()
    return jsonify({'projects': projects})


@bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get project details.

    Returns:
    {
        "project_id": "proj_xxx",
        "requirement": "Build a todo app",
        "status": "completed",
        "result": {...}
    }
    """
    project = task_service.get_project(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify(project)


@bp.route('/<project_id>/status', methods=['GET'])
def get_project_status(project_id):
    """
    Get project status.

    Returns:
    {
        "project_id": "proj_xxx",
        "status": "completed",
        "progress": 100
    }
    """
    status = task_service.get_status(project_id)

    if not status:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify(status)


@bp.route('/<project_id>/files', methods=['GET'])
def list_project_files(project_id):
    """
    List all files in a project.

    Returns:
    {
        "files": [
            {"path": "app.py", "language": "python"},
            {"path": "templates/index.html", "language": "html"}
        ]
    }
    """
    files = task_service.list_files(project_id)

    if files is None:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify({'files': files})


@bp.route('/<project_id>/file/<path:file_path>', methods=['GET'])
def get_project_file(project_id, file_path):
    """
    Get file content.

    Returns:
    {
        "path": "app.py",
        "content": "...",
        "language": "python"
    }
    """
    content = task_service.get_file(project_id, file_path)

    if content is None:
        return jsonify({'error': 'File not found'}), 404

    return jsonify(content)


@bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project."""
    success = task_service.delete_project(project_id)

    if not success:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify({'message': 'Project deleted'})
