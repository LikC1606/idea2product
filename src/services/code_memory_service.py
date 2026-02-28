"""Code Memory Service - SQLite-based code snippet storage with AST and symbol table support."""

import ast
import re
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.data_models import CodeSnippet, SymbolTableEntry
from src.utils.logger import get_logger

logger = get_logger(__name__)

_SQLITE_TIMEOUT = 5


class CodeMemoryService:
    """
    Service for storing and retrieving code snippets with AST and symbol table.

    Enhanced from original design to support:
    - Dynamic knowledge graph
    - AST (Abstract Syntax Tree) parsing
    - Global symbol table maintenance
    """

    def __init__(self, db_path: Path):
        """
        Initialize the code memory service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database schema."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to create DB directory: {e}")
            raise

        try:
            conn = sqlite3.connect(self.db_path, timeout=_SQLITE_TIMEOUT)
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to code memory DB: {e}")
            raise

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS code_snippets (
                    id TEXT PRIMARY KEY,
                    function_name TEXT NOT NULL,
                    description TEXT,
                    code TEXT NOT NULL,
                    language TEXT NOT NULL,
                    tags TEXT,
                    usage_count INTEGER DEFAULT 0,
                    project_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS symbol_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol_name TEXT NOT NULL,
                    symbol_type TEXT NOT NULL,
                    module TEXT NOT NULL,
                    signature TEXT,
                    docstring TEXT,
                    line_number INTEGER,
                    project_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol_name, module, project_id)
                )
            """
            )

            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS code_search
                USING fts5(function_name, description, tags)
            """
            )

            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize code memory schema: {e}")
            raise
        finally:
            conn.close()
        logger.info(f"Code memory database initialized at {self.db_path}")

    def add_snippet(self, snippet: CodeSnippet) -> None:
        """Add a code snippet to memory."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=_SQLITE_TIMEOUT)
        except sqlite3.Error as e:
            logger.warning(f"Code memory DB unavailable, skipping add_snippet: {e}")
            return

        try:
            cursor = conn.cursor()

            # Delete old FTS5 row before REPLACE so rowids stay in sync
            # (INSERT OR REPLACE into code_snippets can change rowid)
            cursor.execute(
                "DELETE FROM code_search WHERE rowid IN (SELECT rowid FROM code_snippets WHERE id = ?)",
                (snippet.id,),
            )

            cursor.execute(
                """
                INSERT OR REPLACE INTO code_snippets
                (id, function_name, description, code, language, tags, usage_count, project_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    snippet.id,
                    snippet.function_name,
                    snippet.description,
                    snippet.code,
                    snippet.language,
                    ",".join(snippet.tags),
                    snippet.usage_count,
                    snippet.project_id,
                ),
            )

            cursor.execute(
                """
                INSERT INTO code_search (rowid, function_name, description, tags)
                SELECT rowid, function_name, description, tags FROM code_snippets WHERE id = ?
            """,
                (snippet.id,),
            )

            conn.commit()
        except sqlite3.OperationalError as e:
            logger.warning(f"Code memory DB locked/busy, skipping add_snippet: {e}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Code memory DB error: {e}")
            raise
        finally:
            conn.close()
        logger.debug(f"Added snippet: {snippet.id}")

    def add_snippets_from_file(
        self,
        content: str,
        file_path: str,
        project_id: str,
        purpose: str = "",
    ) -> int:
        """Parse a Python file and add function/class-level snippets. Returns count added."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.debug(f"Skipped parsing {file_path}: syntax error")
            return 0

        module_name = file_path.replace("/", ".").replace("\\", ".").removesuffix(".py")
        count = 0

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                count += self._add_node_snippet(
                    node, content, file_path, project_id, module_name, purpose
                )
            elif isinstance(node, ast.ClassDef):
                count += self._add_class_snippet(
                    node, content, file_path, project_id, module_name, purpose
                )

        return count

    def _add_node_snippet(
        self,
        node: ast.AST,
        content: str,
        file_path: str,
        project_id: str,
        module_name: str,
        purpose: str,
    ) -> int:
        """Add a single function or method as snippet. Returns 1 if added else 0."""
        name = node.name
        if name.startswith("_"):
            return 0
        try:
            code = ast.get_source_segment(content, node) or ""
        except Exception:
            code = ""
        if not code or len(code) < 20:
            return 0

        docstring = ast.get_docstring(node) or ""
        desc = docstring[:200] if docstring else purpose or f"{module_name}.{name}"

        tags = [project_id, module_name, name, "function"]
        snippet_id = f"{project_id}_{file_path.replace('/', '_')}_{name}"

        snippet = CodeSnippet(
            id=snippet_id,
            function_name=name,
            description=desc,
            code=code[:4000],
            language="python",
            tags=tags,
            usage_count=0,
            project_id=project_id,
        )
        self.add_snippet(snippet)
        return 1

    def _add_class_snippet(
        self,
        node: ast.ClassDef,
        content: str,
        file_path: str,
        project_id: str,
        module_name: str,
        purpose: str,
    ) -> int:
        """Add class as snippet and each method as separate snippet (ParentClass.method)."""
        count = 0
        name = node.name
        if name.startswith("_"):
            return 0
        try:
            code = ast.get_source_segment(content, node) or ""
        except Exception:
            code = ""
        if not code or len(code) < 20:
            return 0

        docstring = ast.get_docstring(node) or ""
        desc = docstring[:200] if docstring else purpose or f"{module_name}.{name}"

        tags = [project_id, module_name, name, "class"]
        snippet_id = f"{project_id}_{file_path.replace('/', '_')}_{name}"

        snippet = CodeSnippet(
            id=snippet_id,
            function_name=name,
            description=desc,
            code=code[:4000],
            language="python",
            tags=tags,
            usage_count=0,
            project_id=project_id,
        )
        self.add_snippet(snippet)
        count += 1

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.startswith("_"):
                    continue
                try:
                    method_code = ast.get_source_segment(content, item) or ""
                except Exception:
                    method_code = ""
                if not method_code or len(method_code) < 15:
                    continue
                method_doc = ast.get_docstring(item) or ""
                method_desc = method_doc[:200] if method_doc else f"{name}.{item.name}"
                method_tags = [project_id, module_name, name, item.name, "method"]
                method_snippet_id = (
                    f"{project_id}_{file_path.replace('/', '_')}_{name}_{item.name}"
                )
                method_snippet = CodeSnippet(
                    id=method_snippet_id,
                    function_name=f"{name}.{item.name}",
                    description=method_desc,
                    code=method_code[:4000],
                    language="python",
                    tags=method_tags,
                    usage_count=0,
                    project_id=project_id,
                )
                self.add_snippet(method_snippet)
                count += 1

        return count

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize FTS5 query to avoid syntax errors (bare -, *, etc.)."""
        if not query or not query.strip():
            return ""
        # Remove or escape FTS5 operators that can cause errors when used alone
        q = query.strip()
        q = re.sub(r'\*+', " ", q)
        q = re.sub(r'\s+-\s*$', "", q)
        return q.strip() or ""

    def search_snippets(
        self,
        query: str,
        limit: int = 5,
        project_id: Optional[str] = None,
        cross_project: bool = False,
    ) -> List[CodeSnippet]:
        """Search for code snippets using full-text search.
        When project_id is set, prefers snippets from that project; if cross_project
        and no results, falls back to other projects."""
        safe_query = self._sanitize_fts_query(query)
        if not safe_query:
            return []

        try:
            conn = sqlite3.connect(self.db_path, timeout=_SQLITE_TIMEOUT)
        except sqlite3.Error as e:
            logger.warning(f"Code memory DB unavailable: {e}")
            return []

        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if project_id:
                cursor.execute(
                    """
                    SELECT s.* FROM code_snippets s
                    JOIN code_search ON s.rowid = code_search.rowid
                    WHERE code_search MATCH ? AND s.project_id = ?
                    ORDER BY s.usage_count DESC
                    LIMIT ?
                """,
                    (safe_query, project_id, limit),
                )
                rows = cursor.fetchall()
                if not rows and cross_project:
                    cursor.execute(
                        """
                        SELECT s.* FROM code_snippets s
                        JOIN code_search ON s.rowid = code_search.rowid
                        WHERE code_search MATCH ?
                        ORDER BY s.usage_count DESC
                        LIMIT ?
                    """,
                        (safe_query, limit),
                    )
                    rows = cursor.fetchall()
            else:
                cursor.execute(
                    """
                    SELECT s.* FROM code_snippets s
                    JOIN code_search ON s.rowid = code_search.rowid
                    WHERE code_search MATCH ?
                    ORDER BY s.usage_count DESC
                    LIMIT ?
                """,
                    (safe_query, limit),
                )
                rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            logger.warning(f"Code memory FTS query error: {e}")
            return []
        except sqlite3.Error as e:
            logger.warning(f"Code memory DB error during search: {e}")
            return []
        finally:
            conn.close()

        snippets = [self._row_to_snippet(row) for row in rows]
        for s in snippets:
            self.increment_usage(s.id)
        return snippets

    def increment_usage(self, snippet_id: str) -> None:
        """Increment usage_count for a snippet (used when search returns it)."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=_SQLITE_TIMEOUT)
        except sqlite3.Error as e:
            logger.debug(f"Code memory DB unavailable for increment: {e}")
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE code_snippets SET usage_count = usage_count + 1 WHERE id = ?",
                (snippet_id,),
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.debug(f"Code memory increment failed: {e}")
        finally:
            conn.close()

    def add_symbol(self, symbol: SymbolTableEntry, project_id: str) -> None:
        """Add a symbol to the symbol table (Interface-First support)."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=_SQLITE_TIMEOUT)
        except sqlite3.Error as e:
            logger.warning(f"Code memory DB unavailable: {e}")
            return

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO symbol_table
                (symbol_name, symbol_type, module, signature, docstring, line_number, project_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    symbol.symbol_name,
                    symbol.symbol_type,
                    symbol.module,
                    symbol.signature,
                    symbol.docstring,
                    symbol.line_number,
                    project_id,
                ),
            )

            conn.commit()
        except sqlite3.OperationalError as e:
            logger.warning(f"Code memory DB locked, skipping add_symbol: {e}")
        except sqlite3.Error as e:
            logger.error(f"Code memory add_symbol error: {e}")
            raise
        finally:
            conn.close()
        logger.debug(f"Added symbol: {symbol.symbol_name} in {symbol.module}")

    def add_symbols_from_skeleton(self, skeleton: Any, project_id: str) -> int:
        """Seed symbol table from CodeSkeleton interfaces (pre-generation).
        Enables get_module_signatures to return skeleton definitions before code exists.
        Returns count of symbols added."""
        if skeleton is None:
            return 0
        interfaces = getattr(skeleton, "interfaces", []) or []
        count = 0
        for iface in interfaces:
            module_name = getattr(iface, "module_name", "") or ""
            if not module_name:
                continue
            for fn in getattr(iface, "functions", []) or []:
                if not isinstance(fn, dict):
                    continue
                name = fn.get("name", "")
                if not name:
                    continue
                params = fn.get("params", []) or []
                ret = fn.get("return_type", "Any") or "Any"
                sig = fn.get("signature")
                if not sig:
                    params_str = ", ".join(params)
                    sig = f"def {name}({params_str}) -> {ret}"
                entry = SymbolTableEntry(
                    symbol_name=name,
                    symbol_type="function",
                    module=module_name,
                    signature=sig,
                    docstring="",
                    line_number=0,
                )
                self.add_symbol(entry, project_id)
                count += 1
            for cls in getattr(iface, "classes", []) or []:
                if not isinstance(cls, dict):
                    continue
                name = cls.get("name", "")
                if not name:
                    continue
                entry = SymbolTableEntry(
                    symbol_name=name,
                    symbol_type="class",
                    module=module_name,
                    signature=f"class {name}",
                    docstring="",
                    line_number=0,
                )
                self.add_symbol(entry, project_id)
                count += 1
        if count:
            logger.info(f"Seeded {count} symbols from skeleton for project {project_id}")
        return count

    def get_symbols_by_module(
        self, module: str, project_id: str
    ) -> List[SymbolTableEntry]:
        """Get all symbols for a specific module (Interface-First support)."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=_SQLITE_TIMEOUT)
        except sqlite3.Error as e:
            logger.warning(f"Code memory DB unavailable: {e}")
            return []

        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM symbol_table
                WHERE module = ? AND project_id = ?
                ORDER BY line_number
            """,
                (module, project_id),
            )

            rows = cursor.fetchall()
        except sqlite3.Error as e:
            logger.warning(f"Code memory get_symbols error: {e}")
            return []
        finally:
            conn.close()

        return [self._row_to_symbol(row) for row in rows]

    def _row_to_snippet(self, row: sqlite3.Row) -> CodeSnippet:
        """Convert database row to CodeSnippet."""
        return CodeSnippet(
            id=row["id"],
            function_name=row["function_name"],
            description=row["description"] or "",
            code=row["code"],
            language=row["language"],
            tags=row["tags"].split(",") if row["tags"] else [],
            usage_count=row["usage_count"],
            project_id=row["project_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _row_to_symbol(self, row: sqlite3.Row) -> SymbolTableEntry:
        """Convert database row to SymbolTableEntry."""
        return SymbolTableEntry(
            symbol_name=row["symbol_name"],
            symbol_type=row["symbol_type"],
            module=row["module"],
            signature=row["signature"],
            docstring=row["docstring"],
            line_number=row["line_number"],
        )
