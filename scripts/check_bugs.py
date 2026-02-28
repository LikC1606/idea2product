#!/usr/bin/env python3
"""
Phase 1 & 2 Bug Check Automation for Idea2Product.

Runs ruff, mypy, bandit, AST syntax validation, and pattern-based grep searches.
Outputs Markdown report suitable for merging into docs/BUG_REPORT.md.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Directories to check (exclude data/projects, venv, etc.)
CHECK_DIRS = ["src", "config", "tests"]
# Bandit only scans src and config (not tests - benchmark code uses subprocess etc.)
BANDIT_DIRS = ["src", "config"]
EXCLUDE_PATTERNS = ["data/projects", "venv", "__pycache__", ".pytest_cache"]

# Allowlist: (file_substring, pattern_name) - findings matching both are skipped
PATTERN_ALLOWLIST = [
    ("preview_service", "pop_mutation"),
    ("task_service", "pop_mutation"),
    ("file_utils.py", "unsafe_read"),
    ("file_utils.py", "unsafe_write"),
]


def should_skip(path: Path) -> bool:
    """Skip generated/excluded paths."""
    s = path.as_posix()
    return any(pat in s for pat in EXCLUDE_PATTERNS)


def run_ruff(target_dirs: list[str]) -> list[dict[str, Any]]:
    """Run ruff check and parse output."""
    findings = []
    cmd = None
    for c in [["ruff", "check"], [sys.executable, "-m", "ruff", "check"]]:
        try:
            result = subprocess.run(
                c + target_dirs,
                capture_output=True,
                text=True,
                timeout=60,
            )
            cmd = c
            break
        except FileNotFoundError:
            continue
    if cmd is None:
        findings.append({"tool": "ruff", "error": "ruff not found"})
        return findings
    try:
        for line in result.stdout.splitlines():
            if ":" in line:
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    findings.append({
                        "file": parts[0],
                        "line": int(parts[1]) if parts[1].isdigit() else 0,
                        "code": parts[2].strip() if len(parts) > 2 else "",
                        "message": parts[3].strip() if len(parts) > 3 else "",
                        "tool": "ruff",
                    })
    except Exception as e:
        findings.append({"tool": "ruff", "error": str(e)})
    return findings


def run_mypy(target_dirs: list[str]) -> list[dict[str, Any]]:
    """Run mypy and parse output. Uses current Python env to avoid version mismatch."""
    findings = []
    last_error = None
    for cmd in [[sys.executable, "-m", "mypy"] + target_dirs, ["mypy"] + target_dirs]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            for line in (result.stdout + result.stderr).splitlines():
                if ": error:" in line:
                    match = re.match(r"^([^:]+):(\d+): error: (.+)$", line)
                    if match:
                        findings.append({
                            "file": match.group(1),
                            "line": int(match.group(2)),
                            "message": match.group(3),
                            "tool": "mypy",
                        })
            return findings
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            last_error = e
            continue
    if last_error:
        findings.append({"tool": "mypy", "error": str(last_error)})
    return findings


def run_bandit(target_dirs: list[str]) -> list[dict[str, Any]]:
    """Run bandit security scanner and parse JSON output."""
    findings = []
    for cmd in [
        ["bandit", "-r"] + target_dirs + ["-f", "json", "-q"],
        [sys.executable, "-m", "bandit", "-r"] + target_dirs + ["-f", "json", "-q"],
    ]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            out = result.stdout.strip() if result.stdout else ""
            if not out:
                continue
            data = json.loads(out)
            for r in data.get("results", []):
                findings.append({
                    "file": r.get("filename", "").replace("\\", "/"),
                    "line": r.get("line_number", 0),
                    "message": f"{r.get('issue_severity', '')} | {r.get('issue_text', '')}",
                    "severity": r.get("issue_severity", ""),
                    "tool": "bandit",
                })
            return findings
        except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
            continue
    return findings


def ast_syntax_check(target_dirs: list[str]) -> list[dict[str, Any]]:
    """Validate Python syntax via ast.parse()."""
    findings = []
    root = Path.cwd()
    for d in target_dirs:
        base = root / d
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if should_skip(path):
                continue
            try:
                ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as e:
                findings.append({
                    "file": str(path),
                    "line": e.lineno or 0,
                    "message": str(e.msg),
                    "tool": "ast",
                })
    return findings


# Pattern name -> (regex, category)
PATTERNS = [
    ("bare_except", r"except\s*:", "潜在风险"),
    ("index_0", r"\.choices\[0\]|\.split\([^)]+\)\[1\]", "逻辑级"),
    ("content_access", r"\.(message\.)?content(?!\s*=)", "逻辑级"),
    ("pop_mutation", r"\.pop\s*\(", "潜在风险"),
    ("div_by_len", r"/\s*len\s*\(|/\s*[a-zA-Z_]+\s*\[", "逻辑级"),
    ("hardcoded_python", r'\[\s*["\']python["\']\s*,', "运行级"),
    ("subprocess_os", r"subprocess\.os\.", "运行级"),
    ("unsafe_read", r"\.read_text\s*\(", "运行级"),
    ("unsafe_write", r"\.write_text\s*\(", "运行级"),
]


def _is_allowlisted(rel_path: str, pattern_name: str) -> bool:
    """Check if (file, pattern) is in allowlist."""
    rel_norm = rel_path.replace("\\", "/")
    for file_sub, pat_sub in PATTERN_ALLOWLIST:
        if file_sub in rel_norm and pat_sub == pattern_name:
            return True
    return False


def grep_patterns(target_dirs: list[str]) -> list[dict[str, Any]]:
    """Search for dangerous code patterns."""
    findings = []
    root = Path.cwd()
    for d in target_dirs:
        base = root / d
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if should_skip(path):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            try:
                rel_path = str(path.relative_to(root)).replace("\\", "/")
            except ValueError:
                rel_path = str(path).replace("\\", "/")
            for line_no, line in enumerate(text.splitlines(), 1):
                for pat_name, regex, category in PATTERNS:
                    if re.search(regex, line):
                        if _is_allowlisted(rel_path, pat_name):
                            continue
                        findings.append({
                            "file": rel_path,
                            "line": line_no,
                            "pattern": pat_name,
                            "category": category,
                            "snippet": line.strip()[:80],
                        })
                        break  # one finding per line per pattern type
    return findings


def to_markdown(all_findings: dict[str, list]) -> str:
    """Format findings as Markdown."""
    lines = [
        "# Phase 1 Bug Check Report (Automated)",
        "",
        "> Generated by `scripts/check_bugs.py`",
        "",
    ]

    for tool, items in all_findings.items():
        if not items:
            continue
        if any("error" in item for item in items if isinstance(item, dict)):
            lines.append(f"## {tool}")
            lines.append("")
            for item in items:
                if isinstance(item, dict) and "error" in item:
                    lines.append(f"- Error: {item['error']}")
            lines.append("")
            continue

        lines.append(f"## {tool} ({len(items)} findings)")
        lines.append("")

        for item in items:
            if not isinstance(item, dict):
                continue
            f = item.get("file", "")
            ln = item.get("line", 0)
            msg = item.get("message", item.get("snippet", ""))
            cat = item.get("category", item.get("code", item.get("severity", "")))
            lines.append(f"- **{f}** L{ln}: {msg}")
            if cat:
                lines.append(f"  - 类型: {cat}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    """Run all checks and output report."""
    root = Path(__file__).resolve().parent.parent
    if (root / "src").exists():
        os.chdir(root)

    all_findings = {
        "ruff": run_ruff(CHECK_DIRS),
        "mypy": run_mypy(CHECK_DIRS),
        "bandit": run_bandit(BANDIT_DIRS),
        "ast": ast_syntax_check(CHECK_DIRS),
        "patterns": grep_patterns(CHECK_DIRS),
    }

    # Output
    out_format = sys.argv[1] if len(sys.argv) > 1 else "markdown"
    if out_format == "json":
        # Filter to serializable
        out = {k: v for k, v in all_findings.items() if v}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(to_markdown(all_findings))

    has_tool_errors = any(
        isinstance(i, dict) and "error" in i
        for v in all_findings.values()
        for i in (v if isinstance(v, list) else [])
    )
    return 1 if has_tool_errors else 0


if __name__ == "__main__":
    sys.exit(main())
