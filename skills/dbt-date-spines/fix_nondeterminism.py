#!/usr/bin/env python3
"""Find non-deterministic window function hazards in a dbt project.

Scans SQL files for ROW_NUMBER/RANK/DENSE_RANK OVER(...) clauses where the
ORDER BY may not produce a unique ordering, which can cause nondeterministic
results across runs.

This script REPORTS hazards but does not auto-fix them, because choosing the
right tiebreaker column requires knowledge of the database schema.  Use this
to identify which files need manual review.

Usage:
    python3 fix_nondeterminism.py <project_dir>

Example:
    python3 fix_nondeterminism.py ./my_dbt_project

Options:
    --help   Show this help message and exit.
"""

import re
import sys
from pathlib import Path

# Match ROW_NUMBER(), RANK(), DENSE_RANK() followed by OVER(...)
# Captures the window spec inside OVER(...)
WINDOW_FUNC = re.compile(
    r'\b(ROW_NUMBER|RANK|DENSE_RANK)\s*\(\s*\)\s*OVER\s*\(([^)]*)\)',
    re.IGNORECASE | re.DOTALL,
)

# Check if ORDER BY exists within a window spec
ORDER_BY = re.compile(r'\bORDER\s+BY\b', re.IGNORECASE)

SKIP_DIRS = {"dbt_packages", "target", ".git", "__pycache__", "node_modules"}


def find_hazards(project_dir: Path) -> list[dict]:
    """Scan SQL files for window function hazards. Returns list of findings."""
    findings = []
    for sql_file in project_dir.rglob("*.sql"):
        if any(skip in sql_file.parts for skip in SKIP_DIRS):
            continue
        content = sql_file.read_text(encoding="utf-8", errors="replace")
        for match in WINDOW_FUNC.finditer(content):
            func_name = match.group(1).upper()
            window_spec = match.group(2)
            # Find line number
            line_num = content[:match.start()].count("\n") + 1

            if not ORDER_BY.search(window_spec):
                findings.append({
                    "file": str(sql_file.relative_to(project_dir)),
                    "line": line_num,
                    "function": func_name,
                    "issue": "Missing ORDER BY clause",
                    "window_spec": window_spec.strip(),
                })
            else:
                # ORDER BY exists, but may have too few columns.
                # Flag single-column ORDER BY as potentially nondeterministic.
                order_match = re.search(
                    r'ORDER\s+BY\s+(.+)',
                    window_spec,
                    re.IGNORECASE | re.DOTALL,
                )
                if order_match:
                    order_cols = [
                        c.strip()
                        for c in order_match.group(1).split(",")
                        if c.strip()
                    ]
                    if len(order_cols) == 1:
                        findings.append({
                            "file": str(sql_file.relative_to(project_dir)),
                            "line": line_num,
                            "function": func_name,
                            "issue": f"ORDER BY has only 1 column ({order_cols[0]}) - may need tiebreaker",
                            "window_spec": window_spec.strip(),
                        })
    return findings


def main() -> int:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__.strip())
        return 0

    if len(sys.argv) < 2:
        print("Usage: python3 fix_nondeterminism.py <project_dir>")
        print("Run with --help for more details.")
        return 1

    project = Path(sys.argv[1])
    if not project.is_dir():
        print(f"Error: {project} is not a directory")
        return 1

    findings = find_hazards(project)
    if findings:
        print(f"Found {len(findings)} potential nondeterminism hazard(s):\n")
        for i, f in enumerate(findings, 1):
            print(f"{i}. {f['file']}:{f['line']}")
            print(f"   Function: {f['function']}")
            print(f"   Issue: {f['issue']}")
            if f["window_spec"]:
                spec_oneline = " ".join(f["window_spec"].split())
                print(f"   Window: OVER({spec_oneline})")
            print()
        print("Review each hazard and add a tiebreaker column (e.g., primary key)")
        print("to the ORDER BY clause to ensure deterministic results.")
    else:
        print("No nondeterminism hazards found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
