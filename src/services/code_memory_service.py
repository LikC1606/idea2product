"""Code Memory Service - SQLite-based code snippet storage with AST and symbol table support."""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.data_models import CodeSnippet, SymbolTableEntry
from src.utils.logger import get_logger

logger = get_logger(__name__)


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
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Code snippets table
        cursor.execute("""
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
        """)

        # Symbol table (new for Interface-First strategy)
        cursor.execute("""
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
        """)

        # Full-text search virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS code_search
            USING fts5(function_name, description, tags)
        """)

        conn.commit()
        conn.close()
        logger.info(f"Code memory database initialized at {self.db_path}")

    def add_snippet(self, snippet: CodeSnippet) -> None:
        """
        Add a code snippet to memory.

        Args:
            snippet: CodeSnippet to store
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO code_snippets
            (id, function_name, description, code, language, tags, usage_count, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snippet.id,
            snippet.function_name,
            snippet.description,
            snippet.code,
            snippet.language,
            ",".join(snippet.tags),
            snippet.usage_count,
            snippet.project_id,
        ))

        # Update FTS table
        cursor.execute("""
            INSERT OR REPLACE INTO code_search (rowid, function_name, description, tags)
            SELECT rowid, function_name, description, tags FROM code_snippets WHERE id = ?
        """, (snippet.id,))

        conn.commit()
        conn.close()
        logger.debug(f"Added snippet: {snippet.id}")

    def search_snippets(self, query: str, limit: int = 5) -> List[CodeSnippet]:
        """
        Search for code snippets using full-text search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching code snippets
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.* FROM code_snippets s
            JOIN code_search cs ON s.rowid = cs.rowid
            WHERE code_search MATCH ?
            ORDER BY usage_count DESC
            LIMIT ?
        """, (query, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_snippet(row) for row in rows]

    def add_symbol(self, symbol: SymbolTableEntry, project_id: str) -> None:
        """
        Add a symbol to the symbol table (Interface-First support).

        Args:
            symbol: SymbolTableEntry to store
            project_id: Project identifier
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO symbol_table
            (symbol_name, symbol_type, module, signature, docstring, line_number, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol.symbol_name,
            symbol.symbol_type,
            symbol.module,
            symbol.signature,
            symbol.docstring,
            symbol.line_number,
            project_id,
        ))

        conn.commit()
        conn.close()
        logger.debug(f"Added symbol: {symbol.symbol_name} in {symbol.module}")

    def get_symbols_by_module(self, module: str, project_id: str) -> List[SymbolTableEntry]:
        """
        Get all symbols for a specific module (Interface-First support).

        Args:
            module: Module name
            project_id: Project identifier

        Returns:
            List of symbol table entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM symbol_table
            WHERE module = ? AND project_id = ?
            ORDER BY line_number
        """, (module, project_id))

        rows = cursor.fetchall()
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
