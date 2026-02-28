"""Code Mining Service - GitHub code search with adaptation."""

import ast
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
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

    def __init__(
        self,
        github_token: Optional[str] = None,
        search_limit: int = 5,
        cache_path: Optional[Path] = None,
    ):
        """
        Initialize the code mining service.

        Args:
            github_token: GitHub API token (optional but recommended)
            search_limit: Maximum number of search results
            cache_path: Optional path to persist cache across runs (JSON file)
        """
        self.github_token = github_token
        self.search_limit = search_limit
        self.cache_path = Path(cache_path) if cache_path else None
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        if github_token:
            auth = self._auth_header(github_token)
            self.session.headers.update({"Authorization": auth})
        self._cache_maxsize = 100
        self._cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        if self.cache_path and self.cache_path.exists():
            self._load_persisted_cache()

    @staticmethod
    def _auth_header(token: str) -> str:
        """Return Authorization header. Fine-grained tokens use Bearer, classic use token."""
        t = (token or "").strip()
        if t.startswith("github_pat_"):
            return f"Bearer {t}"
        return f"token {t}"

    def _load_persisted_cache(self) -> None:
        """Load cache from disk if cache_path is set."""
        if not self.cache_path or not self.cache_path.exists():
            return
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            items = data.get("items", [])
            for k, v in items[-self._cache_maxsize :]:
                self._cache[k] = v
            logger.debug(f"Loaded {len(self._cache)} entries from code mining cache")
        except Exception as e:
            logger.debug(f"Could not load code mining cache: {e}")

    def _persist_cache(self) -> None:
        """Persist cache to disk if cache_path is set."""
        if not self.cache_path:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            items = list(self._cache.items())
            self.cache_path.write_text(
                json.dumps({"items": items}, ensure_ascii=False, indent=0),
                encoding="utf-8",
            )
        except Exception as e:
            logger.debug(f"Could not persist code mining cache: {e}")

    def search_code(
        self,
        query: str,
        language: str = "python",
        per_page: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search code using GitHub Code Search API. Requires github_token.
        Returns list of {repository, path, name, html_url, ...}.
        """
        if not self.github_token:
            return []

        # Code Search has strict rate limits (9 req/min); use conservatively
        try:
            q = f"{query} language:{language}"
            response = self.session.get(
                f"{self.base_url}/search/code",
                params={"q": q, "per_page": min(per_page, 5)},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15,
            )
            if response.status_code != 200:
                return []
            data = response.json()
            items = []
            for hit in data.get("items", []):
                repo = hit.get("repository") or {}
                if isinstance(repo, dict):
                    full_name = repo.get("full_name", "")
                else:
                    full_name = getattr(repo, "full_name", "") or ""
                items.append(
                    {
                        "repository": hit.get("repository"),
                        "full_name": full_name,
                        "path": hit.get("path", ""),
                        "name": hit.get("name", ""),
                        "html_url": hit.get("html_url", ""),
                        "sha": hit.get("sha", ""),
                    }
                )
            if items:
                logger.info(f"Code search found {len(items)} files")
            return items
        except Exception as e:
            logger.debug(f"Code search failed: {e}")
            return []

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
        logger.info(
            f"Searching GitHub for: {query} (language={language}, min_stars={min_stars})"
        )

        results = []

        # Build search query
        search_query = f"{query} language:{language}"
        params = {"q": search_query, "sort": "stars", "per_page": self.search_limit}

        try:
            # Search repositories (code search has lower rate limits)
            response = self.session.get(
                f"{self.base_url}/search/repositories", params=params, timeout=30
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
                {
                    "name": "flask-restful",
                    "full_name": "flask-restful/flask-restful",
                    "description": "Framework for building REST APIs",
                    "stars": 10000,
                    "url": "https://github.com/flask-restful/flask-restful",
                },
            ],
            "auth": [
                {
                    "name": "flask-jwt-extended",
                    "full_name": "flask-jwt-extended/flask-jwt-extended",
                    "description": "JWT authentication for Flask",
                    "stars": 5000,
                    "url": "https://github.com/flask-jwt-extended/flask-jwt-extended",
                },
            ],
            "database": [
                {
                    "name": "flask-sqlalchemy",
                    "full_name": "pallets/flask-sqlalchemy",
                    "description": "SQLAlchemy integration for Flask",
                    "stars": 3000,
                    "url": "https://github.com/pallets/flask-sqlalchemy",
                },
            ],
            "api": [
                {
                    "name": "requests",
                    "full_name": "psf/requests",
                    "description": "HTTP library for Python",
                    "stars": 50000,
                    "url": "https://github.com/psf/requests",
                },
            ],
            "template": [
                {
                    "name": "jinja",
                    "full_name": "pallets/jinja",
                    "description": "Template engine for Python",
                    "stars": 9000,
                    "url": "https://github.com/pallets/jinja",
                },
            ],
            "html": [
                {
                    "name": "jinja",
                    "full_name": "pallets/jinja",
                    "description": "Template engine for Python",
                    "stars": 9000,
                    "url": "https://github.com/pallets/jinja",
                },
            ],
            "jinja2": [
                {
                    "name": "jinja",
                    "full_name": "pallets/jinja",
                    "description": "Template engine for Python",
                    "stars": 9000,
                    "url": "https://github.com/pallets/jinja",
                },
            ],
            "form": [
                {
                    "name": "flask-wtf",
                    "full_name": "wtforms/flask-wtf",
                    "description": "Form validation and rendering for Flask",
                    "stars": 1500,
                    "url": "https://github.com/wtforms/flask-wtf",
                },
            ],
            "layout": [
                {
                    "name": "jinja",
                    "full_name": "pallets/jinja",
                    "description": "Template engine for Python",
                    "stars": 9000,
                    "url": "https://github.com/pallets/jinja",
                },
            ],
        }

        query_lower = query.lower()
        lang_lower = (language or "").lower()
        for key, patterns in fallback_patterns.items():
            if key in query_lower:
                return patterns
        if lang_lower in ("html", "template", "jinja2", "jinja"):
            return fallback_patterns.get("html", fallback_patterns["template"])

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

    def adapt_with_llm(
        self,
        code: str,
        interface_spec: Dict[str, Any],
        llm_service,
    ) -> str:
        """Use LLM to adapt code to match interface_spec. Falls back to regex adapt on failure."""
        if (
            not llm_service
            or not interface_spec.get("functions")
            and not interface_spec.get("classes")
        ):
            return self.adapt_code_to_interface(code, interface_spec)
        try:
            fns = interface_spec.get("functions", [])[:5]
            clss = interface_spec.get("classes", [])[:3]
            spec_str = "\n".join(
                [
                    f"def {f.get('name')}({', '.join(f.get('params', []))}) -> {f.get('return_type', 'Any')}"
                    for f in fns
                ]
                + [f"class {c.get('name')}" for c in clss]
            )
            prompt = f"""Adapt this Python code to match the required interfaces. Keep the core logic. Only change signatures and imports as needed.

Required interfaces:
{spec_str}

Original code:
```python
{code[:3000]}
```

Return ONLY the adapted Python code, no explanation."""
            result = llm_service.generate(prompt, max_tokens=2000)
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[-1].rsplit("```", 1)[0]
            if result and len(result) > 50:
                return result
        except Exception as e:
            logger.debug(f"LLM adaptation failed: {e}")
        return self.adapt_code_to_interface(code, interface_spec)

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
                    adapted_code = self._adapt_class(adapted_code, class_name, methods)

            logger.info("Code adaptation completed")
            return adapted_code

        except SyntaxError as e:
            logger.warning(f"Failed to parse code for adaptation: {e}")
            return self._simple_adapt(code, interface_spec)

    def _adapt_function(
        self, code: str, func_name: str, params: List[str], return_type: str
    ) -> str:
        """Adapt a function signature to match interface."""
        # Build new signature
        params_str = ", ".join(params)
        new_sig = f"def {func_name}({params_str}) -> {return_type}:"

        # Find and replace old signature
        # Match function definition with any existing params
        pattern = rf"def\s+{func_name}\s*\([^)]*\)\s*(?:->\s*\w+)?\s*:"
        if re.search(pattern, code):
            code = re.sub(pattern, new_sig, code)

        return code

    def _adapt_class(self, code: str, class_name: str, methods: List[str]) -> str:
        """Adapt a class to match interface."""
        # This is a simplified implementation
        # In a full implementation, we would parse and modify the AST

        # Check if class exists
        class_pattern = rf"class\s+{class_name}\s*[:\(]"
        if not re.search(class_pattern, code):
            # Add class wrapper if not present
            method_defs = "\n    ".join(
                [f"def {m.split(':')[0].strip()}(self): pass" for m in methods[:3]]
            )
            class_template = f"""class {class_name}:
    def __init__(self):
        pass
    {method_defs}
"""
            code = class_template + "\n" + code

        return code

    def _simple_adapt(self, code: str, interface_spec: Dict[str, Any]) -> str:
        """Simple text-based adaptation when AST parsing fails."""
        adapted = code

        # Add type hints based on interface
        expected_functions = interface_spec.get("functions", [])
        for expected in expected_functions:
            func_name = expected.get("name")
            return_type = expected.get("return_type", "Any")

            if func_name and return_type != "Any":
                # Add return type hint if missing
                pattern = rf"(def\s+{func_name}\s*\([^)]*\))\s*:"
                replacement = rf"\1 -> {return_type}:"
                adapted = re.sub(pattern, replacement, adapted)

        return adapted

    def search_and_adapt(
        self,
        query: str,
        interface_spec: Dict[str, Any],
        language: str = "python",
        llm_service=None,
        use_llm_adaptation: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub and adapt code to match interface.
        When github_token is set, tries Code Search API first for precise code results.
        Caches results by (query, interface_hash) within session.

        Args:
            query: Search query
            interface_spec: Interface specification to adapt to
            language: Programming language
            llm_service: Optional LLM for adapt_with_llm when use_llm_adaptation=True
            use_llm_adaptation: Use LLM for adaptation (extra API cost)

        Returns:
            List of adapted code snippets with metadata
        """
        cache_key = hashlib.md5(
            (
                query.strip().lower() + json.dumps(interface_spec, sort_keys=True)
            ).encode(),
            usedforsecurity=False,
        ).hexdigest()
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        results = []
        has_interface = bool(
            interface_spec.get("functions") or interface_spec.get("classes")
        )
        adapt_fn = (
            (lambda c, spec: self.adapt_with_llm(c, spec, llm_service))
            if use_llm_adaptation and llm_service and has_interface
            else self.adapt_code_to_interface
        )

        code_hits = self.search_code(query, language, per_page=self.search_limit)
        if code_hits:
            for hit in code_hits:
                full_name = hit.get("full_name", "")
                path = hit.get("path", "")
                if full_name and path:
                    content = self.get_file_content(full_name, path)
                    adapted_code = None
                    status = "found"
                    if content and len(content) > 50 and has_interface:
                        try:
                            adapted_code = adapt_fn(content, interface_spec)
                            status = "adapted"
                        except Exception as e:
                            logger.debug(
                                f"Adaptation failed for {full_name}/{path}: {e}"
                            )
                            adapted_code = content[:2000]
                    elif content and len(content) > 50:
                        adapted_code = content[:2000]
                    repo_info = {
                        "full_name": full_name,
                        "url": hit.get("html_url", ""),
                        "html_url": hit.get("html_url", ""),
                    }
                    results.append(
                        {
                            "repo": repo_info,
                            "adapted_code": adapted_code,
                            "status": status,
                        }
                    )
            if results:
                return results

        search_results = self.search_github(query, language)

        for repo in search_results:
            adapted_code = None
            status = "found"
            full_name = repo.get("full_name", "")

            if full_name:
                # Try common file paths based on language
                if language == "html":
                    candidate_paths = [
                        "templates/index.html",
                        "templates/base.html",
                        "templates/layout.html",
                        "index.html",
                    ]
                else:
                    candidate_paths = [
                        "app.py",
                        "app/__init__.py",
                        "routes.py",
                        "views.py",
                        "models.py",
                    ]
                for cpath in candidate_paths:
                    content = self.get_file_content(full_name, cpath)
                    if content and len(content) > 50:
                        if has_interface and language == "python":
                            try:
                                adapted_code = adapt_fn(content, interface_spec)
                                status = "adapted"
                            except Exception as e:
                                logger.debug(
                                    f"Adaptation failed for {full_name}/{cpath}: {e}"
                                )
                                adapted_code = content[:2000]
                        else:
                            adapted_code = content[:2000]
                        break

            results.append(
                {
                    "repo": repo,
                    "adapted_code": adapted_code,
                    "status": status,
                }
            )

        if len(self._cache) >= self._cache_maxsize and cache_key not in self._cache:
            self._cache.popitem(last=False)
        self._cache[cache_key] = results
        self._cache.move_to_end(cache_key)
        self._persist_cache()
        return results
