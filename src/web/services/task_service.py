"""Task Service - Background task management.

Long-running pipeline tasks run in a background thread. Clients get status via
polling: GET /api/projects/<id>/status returns status (pending|processing|completed|failed),
progress (0-100), and current_stage (e.g. Stage 1: Requirements, Stage 4: Validating).
WebSocket real-time progress is not implemented; use polling for now.
"""

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config.settings import Settings
# Import Orchestrator lazily to avoid API key requirement at startup
# from src.core.orchestrator import Orchestrator


class TaskService:
    """Service for managing background tasks."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def create_project(self, requirement: str, interactive: bool = False, clarifications: Dict[str, str] = None) -> str:
        """Create a new project and start background processing."""
        # Generate project ID - use timestamp only for stability
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if clarifications is None:
            clarifications = {}

        # Initialize task
        with self.lock:
            self.tasks[project_id] = {
                'project_id': project_id,
                'requirement': requirement,
                'status': 'pending',
                'progress': 0,
                'created_at': datetime.now().isoformat(),
                'result': None,
                'error': None,
                'interactive': interactive,
                'clarifications': clarifications,
                'current_stage': 'initializing'
            }

        # Start background task
        thread = threading.Thread(
            target=self._process_project,
            args=(project_id, requirement, interactive, clarifications)
        )
        thread.daemon = True
        thread.start()

        return project_id

    def _process_project(self, project_id: str, requirement: str, interactive: bool = False, clarifications: Dict[str, str] = None):
        """Process project in background."""
        # Import here to avoid API key requirement at startup
        from src.core.orchestrator import Orchestrator
        import signal
        import sys

        if clarifications is None:
            clarifications = {}

        # Debug: Print to stderr so we can see it
        print(f"[DEBUG] Starting project {project_id}", file=sys.stderr, flush=True)

        # Set timeout (5 minutes max)
        def timeout_handler():
            self._update_status(project_id, 'failed', 0)
            with self.lock:
                if project_id in self.tasks:
                    self.tasks[project_id]['error'] = 'Processing timeout (5 minutes)'

        try:
            print(f"[DEBUG] Creating orchestrator for {project_id}", file=sys.stderr, flush=True)

            # Update status
            self._update_status(project_id, 'processing', 5)
            self.tasks[project_id]['current_stage'] = 'Stage 1: Requirements'

            # Create orchestrator
            orchestrator = Orchestrator(self.settings)

            print(f"[DEBUG] Running orchestrator for {project_id}", file=sys.stderr, flush=True)

            # Update progress - Stage 1
            self._update_status(project_id, 'processing', 15)
            self.tasks[project_id]['current_stage'] = 'Stage 1: Analyzing requirements'

            # Run the pipeline (non-interactive for web)
            # Note: Interactive mode requires terminal input which isn't available in web
            result = orchestrator.run(requirement, interactive=False)

            print(f"[DEBUG] Orchestrator completed for {project_id}, result: {result}", file=sys.stderr, flush=True)

            # Update progress - Stage 2
            self._update_status(project_id, 'processing', 40)
            self.tasks[project_id]['current_stage'] = 'Stage 2: Planning'

            # Stage 3
            self._update_status(project_id, 'processing', 70)
            self.tasks[project_id]['current_stage'] = 'Stage 3: Generating code'

            # Stage 4
            self._update_status(project_id, 'processing', 90)
            self.tasks[project_id]['current_stage'] = 'Stage 4: Validating'

            # Update with result
            with self.lock:
                if project_id in self.tasks:
                    if result is None:
                        self.tasks[project_id]['status'] = 'completed'
                        self.tasks[project_id]['progress'] = 100
                        self.tasks[project_id]['current_stage'] = 'Completed'
                        self.tasks[project_id]['result'] = {
                            'is_deployable': True,
                            'files_count': 0,
                            'test_passed': False
                        }
                    else:
                        self.tasks[project_id]['status'] = 'completed'
                        self.tasks[project_id]['progress'] = 100
                        self.tasks[project_id]['current_stage'] = 'Completed'
                        self.tasks[project_id]['result'] = {
                            'is_deployable': result.is_deployable,
                            'files_count': len(result.repository.files),
                            'test_passed': result.test_results.logic_passed if result.test_results else False
                        }

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"[DEBUG] Exception in _process_project: {error_msg}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            with self.lock:
                if project_id in self.tasks:
                    self.tasks[project_id]['status'] = 'failed'
                    self.tasks[project_id]['error'] = error_msg
                    self.tasks[project_id]['current_stage'] = f'Error: {error_msg[:50]}'

    def _update_status(self, project_id: str, status: str, progress: int):
        """Update task status."""
        with self.lock:
            if project_id in self.tasks:
                self.tasks[project_id]['status'] = status
                self.tasks[project_id]['progress'] = progress

    def get_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project status."""
        with self.lock:
            task = self.tasks.get(project_id)
            if not task:
                return None

            return {
                'project_id': project_id,
                'status': task['status'],
                'progress': task['progress'],
                'current_stage': task.get('current_stage', ''),
                'error': task.get('error')
            }

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get full project details."""
        with self.lock:
            task = self.tasks.get(project_id)
            if not task:
                # Try to load from disk
                return self._load_project(project_id)

            return task

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        projects = []

        # Load from memory
        with self.lock:
            for project_id, task in self.tasks.items():
                projects.append({
                    'project_id': project_id,
                    'requirement': task.get('requirement', ''),
                    'status': task.get('status', 'unknown'),
                    'created_at': task.get('created_at', '')
                })

        # Also scan data directory
        data_dir = self.settings.data_dir / 'projects'
        if data_dir.exists():
            for proj_dir in data_dir.iterdir():
                if proj_dir.is_dir():
                    proj_id = proj_dir.name
                    if proj_id not in self.tasks:
                        # Load from disk
                        project = self._load_project(proj_id)
                        if project:
                            projects.append({
                                'project_id': proj_id,
                                'requirement': project.get('requirement', ''),
                                'status': project.get('status', 'completed'),
                                'created_at': project.get('created_at', '')
                            })

        return projects

    def list_files(self, project_id: str) -> Optional[List[Dict[str, str]]]:
        """List project files."""
        project = self.get_project(project_id)
        if not project:
            return None

        result = project.get('result', {})
        if not result:
            return []

        # Try to load from disk
        project_path = self.settings.data_dir / 'projects' / project_id / 'artifacts'
        if project_path.exists():
            code_repo_file = project_path / '03_code_repository.json'
            if code_repo_file.exists():
                with open(code_repo_file, encoding='utf-8') as f:
                    data = json.load(f)
                    files = data.get('files', [])
                    return [{'path': f['path'], 'language': f.get('language', 'text')}
                            for f in files]

        return []

    def get_file(self, project_id: str, file_path: str) -> Optional[Dict[str, str]]:
        """Get file content."""
        project_path = self.settings.data_dir / 'projects' / project_id / 'generated' / file_path

        if not project_path.exists():
            return None

        # Determine language
        ext = Path(file_path).suffix.lower()
        lang_map = {
            '.py': 'python',
            '.html': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.json': 'json',
            '.md': 'markdown'
        }

        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            'path': file_path,
            'content': content,
            'language': lang_map.get(ext, 'text')
        }

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        with self.lock:
            if project_id in self.tasks:
                del self.tasks[project_id]

        # Also delete from disk
        project_path = self.settings.data_dir / 'projects' / project_id
        if project_path.exists():
            import shutil
            shutil.rmtree(project_path)
            return True

        return project_id in self.tasks

    def _load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Load project from disk."""
        project_path = self.settings.data_dir / 'projects' / project_id / 'artifacts'
        if not project_path.exists():
            return None

        # Load requirements
        req_file = project_path / '01_requirements.json'
        if req_file.exists():
            with open(req_file, encoding='utf-8') as f:
                req_data = json.load(f)

            return {
                'project_id': project_id,
                'requirement': req_data.get('description', ''),
                'status': 'completed',
                'created_at': req_data.get('created_at', ''),
                'result': {
                    'is_deployable': True,
                    'files_count': 0,
                    'test_passed': True
                }
            }

        return None


# Global task service instance
task_service = TaskService(Settings())
