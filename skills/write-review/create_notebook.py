#!/usr/bin/env python3
"""Create a new SignalPilot notebook with boilerplate.

Usage:
    python scripts/create_notebook.py my_notebook.py
    python scripts/create_notebook.py my_notebook.py --title "My Dashboard"
    python scripts/create_notebook.py my_notebook.py --width full --setup "import pandas as pd"
    python scripts/create_notebook.py path/to/notebook.py --cells 3 --sp-init
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path


def build_notebook(
    *,
    title: str | None = None,
    width: str = "full",
    num_cells: int = 1,
    setup_code: str | None = None,
    sp_init: bool = False,
) -> str:
    cells: list[str] = []

    # Setup cell (always first)
    setup_lines = ["import signalpilot as sp"]
    if setup_code:
        setup_lines.append(setup_code)
    setup_body = "\n    ".join(setup_lines)
    cells.append(
        f"@app.cell\n"
        f"def _():\n"
        f"    {setup_body}\n"
        f"\n"
        f"    return (sp,)"
    )

    # Optional: sp.init() cell for data SDK
    if sp_init:
        cells.append(
            "@app.cell\n"
            "def _(sp):\n"
            "    sp.init()\n"
            "    connections = sp.connections()\n"
            "    print(f\"Available connections: {connections}\")\n"
            "    return"
        )

    # Optional: title cell
    if title:
        cells.append(
            "@app.cell\n"
            "def _(sp):\n"
            f'    sp.md("""\n'
            f"    # {title}\n"
            f'    """)\n'
            "    return"
        )

    # Empty cells
    for _ in range(num_cells):
        cells.append(
            "@app.cell\n"
            "def _():\n"
            "    return"
        )

    # Build the full file
    width_arg = f'width="{width}"' if width != "medium" else ""
    app_args = width_arg
    app_line = f"app = sp.App({app_args})" if app_args else "app = sp.App()"

    parts = [
        "import signalpilot as sp",
        "",
        '__generated_with = "0.1.0"',
        app_line,
        "",
        "",
    ]

    parts.append("\n\n\n".join(cells))
    parts.append("")
    parts.append("")
    parts.append('if __name__ == "__main__":')
    parts.append("    app.run()")
    parts.append("")

    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a new SignalPilot notebook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python create_notebook.py dashboard.py
              python create_notebook.py dashboard.py --title "Revenue Dashboard"
              python create_notebook.py analysis.py --sp-init --cells 3
              python create_notebook.py etl.py --setup "import pandas as pd\\nimport numpy as np"
        """),
    )
    parser.add_argument(
        "filename",
        help="Path for the new notebook file (e.g., my_notebook.py)",
    )
    parser.add_argument(
        "--title",
        help="Add a markdown title cell",
    )
    parser.add_argument(
        "--width",
        default="full",
        choices=["full", "medium", "compact", "columns"],
        help="App width (default: full)",
    )
    parser.add_argument(
        "--cells",
        type=int,
        default=1,
        help="Number of empty cells to add (default: 1)",
    )
    parser.add_argument(
        "--setup",
        help="Additional imports for the setup cell (e.g., 'import pandas as pd')",
    )
    parser.add_argument(
        "--sp-init",
        action="store_true",
        help="Add a cell with sp.init() for SignalPilot data SDK",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file",
    )

    args = parser.parse_args()
    path = Path(args.filename)

    if path.exists() and not args.force:
        print(f"Error: {path} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    content = build_notebook(
        title=args.title,
        width=args.width,
        num_cells=args.cells,
        setup_code=args.setup,
        sp_init=args.sp_init,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    abs_path = path.resolve()
    print(f"Created: {abs_path}")
    print(f"Directory: {abs_path.parent}")


if __name__ == "__main__":
    main()
