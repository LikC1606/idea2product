"""Stage 4 Testing Tools - LangChain Tools for API Testing."""

import json
import re
import sys
from pathlib import Path
from typing import Optional

import requests


def get_testing_tools(project_path: str, port: int = 5555):
    """Get LangChain tools for frontend testing."""
    from langchain_core.tools import tool

    @tool
    def list_files(path: str = ".") -> str:
        """List files in a directory.

        Args:
            path: Directory path relative to project root

        Returns:
            List of files in the directory
        """
        base = Path(project_path)
        target = base / path

        if not target.exists():
            return f"Directory not found: {path}"

        if target.is_file():
            return str(target.relative_to(base))

        files = []
        for item in sorted(target.rglob("*")):
            if item.is_file():
                rel = item.relative_to(base)
                files.append(str(rel))

        return "\n".join(files) if files else "No files found"

    @tool
    def read_file(path: str) -> str:
        """Read a file's content.

        Args:
            path: File path relative to project root

        Returns:
            File content
        """
        base = Path(project_path)
        target = base / path

        if not target.exists():
            return f"File not found: {path}"

        try:
            content = target.read_text(encoding="utf-8")
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    @tool
    def read_html_file(path: str) -> str:
        """Read an HTML template file with highlighted JavaScript.

        Args:
            path: HTML file path relative to project root

        Returns:
            HTML content with JavaScript sections
        """
        base = Path(project_path)
        target = base / path

        if not target.exists():
            return f"File not found: {path}"

        try:
            content = target.read_text(encoding="utf-8")
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    @tool
    def test_api(
        method: str,
        path: str,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> str:
        """Test an API endpoint.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: URL path (e.g., /api/blogs or /api/blogs/1)
            data: Request body as JSON dict
            headers: Additional headers dict
            params: URL query parameters dict

        Returns:
            JSON response with status code and body

        Examples:
            test_api("POST", "/api/blogs", {"title": "Test", "content": "Hello"})
            test_api("GET", "/api/blogs")
            test_api("GET", "/api/blogs/1")
            test_api("PUT", "/api/blogs/1", {"title": "Updated"})
            test_api("DELETE", "/api/blogs/1")
        """
        url = f"http://localhost:{port}{path}"

        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)

        try:
            if method.upper() == "GET":
                response = requests.get(
                    url, params=params, headers=default_headers, timeout=10
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, json=data, params=params, headers=default_headers, timeout=10
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, json=data, params=params, headers=default_headers, timeout=10
                )
            elif method.upper() == "PATCH":
                response = requests.patch(
                    url, json=data, params=params, headers=default_headers, timeout=10
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, params=params, headers=default_headers, timeout=10
                )
            else:
                return json.dumps({"error": f"Unsupported method: {method}"})

            # Try to parse JSON response
            try:
                response_data = response.json()
            except (ValueError, TypeError):
                response_data = response.text

            result = {
                "status_code": response.status_code,
                "ok": response.ok,
                "response": response_data,
                "headers": {
                    k: v
                    for k, v in response.headers.items()
                    if k.lower() not in ["content-encoding", "transfer-encoding"]
                },
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        except requests.exceptions.ConnectionError as e:
            return json.dumps({"error": f"Connection failed: {e}"}, ensure_ascii=False)
        except requests.exceptions.Timeout as e:
            return json.dumps({"error": f"Timeout: {e}"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    return [list_files, read_file, read_html_file, test_api]


def get_fix_tools(project_path: str, port: int = 5555):
    """Get LangChain tools for code fixing."""
    import subprocess
    import time
    import os

    from langchain_core.tools import tool

    _process = {"proc": None}

    @tool
    def try_run(port: int = 5555) -> str:
        """Try to run app.py and check if it works.

        Args:
            port: Port to run the app on (default 5555)

        Returns:
            JSON string with status: success or error
        """
        base = Path(project_path)

        # Find entry file
        entry_file = None
        if (base / "app.py").exists():
            entry_file = "app.py"
        elif (base / "run.py").exists():
            entry_file = "run.py"

        if not entry_file:
            return json.dumps({"status": "error", "message": "No entry point found (app.py or run.py)"})

        # Stop previous process if any
        if _process.get("proc") and _process["proc"].poll() is None:
            _process["proc"].terminate()
            try:
                _process["proc"].wait(timeout=3)
            except subprocess.TimeoutExpired:
                _process["proc"].kill()
            time.sleep(1)

        # Set port environment
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["FLASK_ENV"] = "testing"

        proc = None
        try:
            proc = subprocess.Popen(
                [sys.executable, entry_file],
                cwd=str(base),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            _process["proc"] = proc

            time.sleep(4)

            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                error_msg = stderr[:2000] if stderr else stdout[:2000]
                return json.dumps({
                    "status": "error",
                    "message": f"App exited immediately:\n{error_msg}"
                })

            try:
                import requests as req
                response = req.get(f"http://localhost:{port}/", timeout=5)
                if response.status_code < 500:
                    return json.dumps({
                        "status": "success",
                        "message": "App started successfully"
                    })
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"App returned status {response.status_code}"
                    })
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Cannot connect to app: {str(e)}"
                })

        except Exception as e:
            if proc is not None and proc.poll() is None:
                proc.terminate()
            return json.dumps({
                "status": "error",
                "message": f"Failed to start app: {str(e)}"
            })

    @tool
    def write_file(path: str, content: str) -> str:
        """Write content to a file.

        Args:
            path: File path relative to project root
            content: File content to write

        Returns:
            JSON string with status
        """
        base = Path(project_path)
        target = base / path

        # Create parent directories if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        try:
            target.write_text(content, encoding="utf-8")
            return json.dumps({
                "status": "success",
                "path": path,
                "message": f"File written successfully"
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "path": path,
                "message": f"Failed to write file: {str(e)}"
            })

    @tool
    def list_files(path: str = ".") -> str:
        """List files in a directory.

        Args:
            path: Directory path relative to project root

        Returns:
            List of files in the directory
        """
        base = Path(project_path)
        target = base / path

        if not target.exists():
            return f"Directory not found: {path}"

        if target.is_file():
            return str(target.relative_to(base))

        files = []
        for item in sorted(target.rglob("*")):
            if item.is_file():
                rel = item.relative_to(base)
                files.append(str(rel))

        return "\n".join(files) if files else "No files found"

    @tool
    def read_file(path: str) -> str:
        """Read a file's content.

        Args:
            path: File path relative to project root

        Returns:
            File content
        """
        base = Path(project_path)
        target = base / path

        if not target.exists():
            return f"File not found: {path}"

        try:
            content = target.read_text(encoding="utf-8")
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    return [try_run, write_file, list_files, read_file]
