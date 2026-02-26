"""Code Mining Service - GitHub code search with adaptation."""

import ast
import re
from typing import List, Optional, Dict, Any
import requests
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeMiningService:
    """
    Service for mining code from GitHub with adaptation support.

    Enhanced from original design to support:
    - Adaptive refactoring based on project interface specifications
    - Seamless integration with current architecture
    """

    def __init__(self, github_token: Optional[str] = None, search_limit: int = 5):
        """
        Initialize the code mining service.

        Args:
            github_token: GitHub API token (optional but recommended)
            search_limit: Maximum number of search results
        """
        self.github_token = github_token
        self.search_limit = search_limit
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        if github_token:
            self.session.headers.update({"Authorization": f"token {github_token}"})

    def search_github(
        self,
        query: str,
        language: str = "python",
        min_stars: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub for code snippets.

        Args:
            query: Search query
            language: Programming language filter
            min_stars: Minimum repository stars

        Returns:
            List of search results with code content
        """
        logger.info(f"Searching GitHub for: {query} (language={language}, min_stars={min_stars})")

        results = []

        # Build search query
        search_query = f"{query} language:{language}"
        params = {
            "q": search_query,
            "sort": "stars",
            "per_page": self.search_limit
        }

        try:
            # Search repositories (code search has lower rate limits)
            response = self.session.get(
                f"{self.base_url}/search/repositories",
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                for repo in data.get("items", []):
                    if repo.get("stargazers_count", 0) >= min_stars:
                        # Get repository info
                        repo_result = {
                            "name": repo.get("name"),
                            "full_name": repo.get("full_name"),
                            "description": repo.get("description"),
                            "stars": repo.get("stargazers_count"),
                            "url": repo.get("html_url"),
                            "language": repo.get("language"),
                        }
                        results.append(repo_result)

                logger.info(f"Found {len(results)} repositories")

            elif response.status_code == 403:
                logger.warning("GitHub API rate limit exceeded")
                # Fallback to sample results
                results = self._fallback_search(query, language)
            else:
                logger.warning(f"GitHub API error: {response.status_code}")
                results = self._fallback_search(query, language)

        except requests.exceptions.RequestException as e:
            logger.warning(f"GitHub search failed: {e}")
            results = self._fallback_search(query, language)

        return results

    def _fallback_search(self, query: str, language: str) -> List[Dict[str, Any]]:
        """Provide fallback results when GitHub API is unavailable."""
        # Common patterns for common features
        fallback_patterns = {
            "crud": [
                {"name": "flask-restful", "full_name": "flask-restful/flask-restful",
                 "description": "Framework for building REST APIs", "stars": 10000, "url": "https://github.com/flask-restful/flask-restful"},
            ],
            "auth": [
                {"name": "flask-jwt-extended", "full_name": "flask-jwt-extended/flask-jwt-extended",
                 "description": "JWT authentication for Flask", "stars": 5000, "url": "https://github.com/flask-jwt-extended/flask-jwt-extended"},
            ],
            "database": [
                {"name": "flask-sqlalchemy", "full_name": "pallets/flask-sqlalchemy",
                 "description": "SQLAlchemy integration for Flask", "stars": 3000, "url": "https://github.com/pallets/flask-sqlalchemy"},
            ],
            "api": [
                {"name": "requests", "full_name": "psf/requests",
                 "description": "HTTP library for Python", "stars": 50000, "url": "https://github.com/psf/requests"},
            ],
        }

        query_lower = query.lower()
        for key, patterns in fallback_patterns.items():
            if key in query_lower:
                return patterns

        return []

    def get_file_content(self, repo: str, path: str) -> Optional[str]:
        """
        Get file content from a GitHub repository.

        Args:
            repo: Repository full name (e.g., "owner/repo")
            path: File path in repository

        Returns:
            File content as string, or None if failed
        """
        try:
            url = f"{self.base_url}/repos/{repo}/contents/{path}"
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get("encoding") == "base64":
                    import base64
                    return base64.b64decode(data["content"]).decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to get file content: {e}")

        return None

    def adapt_code_to_interface(
        self,
        code: str,
        interface_spec: Dict[str, Any],
    ) -> str:
        """
        Adapt external code to match project interface specifications.

        This is the new capability from plan.txt update:
        "基于当前项目的接口规范进行适配性重构"

        Args:
            code: External code snippet
            interface_spec: Project interface specification with expected function signatures

        Returns:
            Adapted code that matches the interface specification
        """
        logger.info("Adapting external code to project interfaces")

        try:
            # Parse the external code
            tree = ast.parse(code)

            # Extract function signatures from interface spec
            expected_functions = interface_spec.get("functions", [])
            expected_classes = interface_spec.get("classes", [])

            adapted_code = code

            # Adapt function signatures
            for expected in expected_functions:
                func_name = expected.get("name")
                params = expected.get("params", [])
                return_type = expected.get("return_type", "Any")

                if func_name:
                    # Find and replace function signature
                    adapted_code = self._adapt_function(
                        adapted_code, func_name, params, return_type
                    )

            # Adapt class interfaces
            for expected in expected_classes:
                class_name = expected.get("name")
                methods = expected.get("methods", [])

                if class_name:
                    adapted_code = self._adapt_class(
                        adapted_code, class_name, methods
                    )

            logger.info("Code adaptation completed")
            return adapted_code

        except SyntaxError as e:
            logger.warning(f"Failed to parse code for adaptation: {e}")
            return self._simple_adapt(code, interface_spec)

    def _adapt_function(
        self,
        code: str,
        func_name: str,
        params: List[str],
        return_type: str
    ) -> str:
        """Adapt a function signature to match interface."""
        # Build new signature
        params_str = ", ".join(params)
        new_sig = f"def {func_name}({params_str}) -> {return_type}:"

        # Find and replace old signature
        # Match function definition with any existing params
        pattern = rf'def\s+{func_name}\s*\([^)]*\)\s*(?:->\s*\w+)?\s*:'
        if re.search(pattern, code):
            code = re.sub(pattern, new_sig, code)

        return code

    def _adapt_class(
        self,
        code: str,
        class_name: str,
        methods: List[str]
    ) -> str:
        """Adapt a class to match interface."""
        # This is a simplified implementation
        # In a full implementation, we would parse and modify the AST

        # Check if class exists
        class_pattern = rf'class\s+{class_name}\s*[:\(]'
        if not re.search(class_pattern, code):
            # Add class wrapper if not present
            method_defs = "\n    ".join([
                f"def {m.split(':')[0].strip()}(self): pass"
                for m in methods[:3]
            ])
            class_template = f"""class {class_name}:
    def __init__(self):
        pass
    {method_defs}
"""
            code = class_template + "\n" + code

        return code

    def _simple_adapt(
        self,
        code: str,
        interface_spec: Dict[str, Any]
    ) -> str:
        """Simple text-based adaptation when AST parsing fails."""
        adapted = code

        # Add type hints based on interface
        expected_functions = interface_spec.get("functions", [])
        for expected in expected_functions:
            func_name = expected.get("name")
            return_type = expected.get("return_type", "Any")

            if func_name and return_type != "Any":
                # Add return type hint if missing
                pattern = rf'(def\s+{func_name}\s*\([^)]*\))\s*:'
                replacement = rf'\1 -> {return_type}:'
                adapted = re.sub(pattern, replacement, adapted)

        return adapted

    def search_and_adapt(
        self,
        query: str,
        interface_spec: Dict[str, Any],
        language: str = "python",
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub and adapt code to match interface.

        Combines search and adaptation: when actual file content can be fetched,
        it adapts signatures to match the project's interface_spec.

        Args:
            query: Search query
            interface_spec: Interface specification to adapt to
            language: Programming language

        Returns:
            List of adapted code snippets with metadata
        """
        results = []
        has_interface = bool(interface_spec.get("functions") or interface_spec.get("classes"))

        search_results = self.search_github(query, language)

        for repo in search_results:
            adapted_code = None
            status = "found"
            full_name = repo.get("full_name", "")

            if has_interface and full_name:
                # Try common Flask file paths to fetch actual code
                candidate_paths = ["app.py", "app/__init__.py", "routes.py", "views.py", "models.py"]
                for cpath in candidate_paths:
                    content = self.get_file_content(full_name, cpath)
                    if content and len(content) > 50:
                        try:
                            adapted_code = self.adapt_code_to_interface(content, interface_spec)
                            status = "adapted"
                        except Exception as e:
                            logger.debug(f"Adaptation failed for {full_name}/{cpath}: {e}")
                            adapted_code = None
                        break

            results.append({
                "repo": repo,
                "adapted_code": adapted_code,
                "status": status,
            })

        return results
