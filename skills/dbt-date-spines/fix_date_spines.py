#!/usr/bin/env python3
"""Fix date spine hazards in a dbt project.

Scans all .sql files for nondeterministic date references (current_date,
current_timestamp, now(), getdate(), sysdate) and replaces them with a
literal date cast.  Skips vendored directories (dbt_packages, target, etc.).

Usage:
    python3 fix_date_spines.py <project_dir> <replacement_date>

Example:
    python3 fix_date_spines.py ./my_dbt_project 2024-01-31

Options:
    --help   Show this help message and exit.
"""

import re
import sys
from pathlib import Path

HAZARD_PATTERNS = [
    re.compile(r'\bcurrent_date\b', re.IGNORECASE),
    re.compile(r'\bcurrent_timestamp\b', re.IGNORECASE),
    re.compile(r'\bnow\s*\(\s*\)', re.IGNORECASE),
    re.compile(r'\bgetdate\s*\(\s*\)', re.IGNORECASE),
    re.compile(r'\bsysdate\b', re.IGNORECASE),
]

SKIP_DIRS = {"dbt_packages", "target", ".git", "__pycache__", "node_modules"}


def scan_and_fix(project_dir: Path, replacement_date: str) -> list[str]:
    """Find and fix date hazards. Returns list of fixed file paths."""
    fixed = []
    for sql_file in project_dir.rglob("*.sql"):
        if any(skip in sql_file.parts for skip in SKIP_DIRS):
            continue
        content = sql_file.read_text(encoding="utf-8", errors="replace")
        new_content = content
        for pattern in HAZARD_PATTERNS:
            new_content = pattern.sub(f"'{replacement_date}'::date", new_content)
        if new_content != content:
            sql_file.write_text(new_content, encoding="utf-8")
            fixed.append(str(sql_file.relative_to(project_dir)))
    return fixed


def main() -> int:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__.strip())
        return 0

    if len(sys.argv) < 3:
        print("Usage: python3 fix_date_spines.py <project_dir> <replacement_date>")
        print("Run with --help for more details.")
        return 1

    project = Path(sys.argv[1])
    date = sys.argv[2]

    if not project.is_dir():
        print(f"Error: {project} is not a directory")
        return 1

    # Basic date format sanity check
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        print(f"Warning: '{date}' does not look like YYYY-MM-DD — proceeding anyway.")

    fixed = scan_and_fix(project, date)
    if fixed:
        print(f"Fixed {len(fixed)} file(s):")
        for f in fixed:
            print(f"  - {f}")
    else:
        print("No date hazards found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
