"""Stage 4 Testing Tools - LangChain Tools for API Testing."""

import json
import re
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
            except:
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
