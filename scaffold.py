#!/usr/bin/env python
"""
scaffold.py – Data Engineering Template Scaffold

This script generates the full project structure for this repository.

How to use:
1. (Optional) Copy this file outside your current project if you want to scaffold a new project.
2. Run: python scaffold.py --name <your_project_name>
   - Use --force to overwrite files in a non-empty directory.
   - Use --no-git to skip git initialization.

See README.md for more details.

Note: This script is for educational and template purposes. It will not modify your current project unless you run it with the appropriate arguments.
"""

# ...existing code from setup_project-DeepSeek-v3_1.py...

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent

DEFAULT_PROJECT_NAME = "de_template"

# ...existing code (all functions and main logic unchanged)...

def main() -> None:
    args = parse_args()

    cwd = Path.cwd()
    print(f"Current directory: {cwd}")

    project_name = args.name or DEFAULT_PROJECT_NAME
    if not args.name:
        project_name = ask("Project name", DEFAULT_PROJECT_NAME)

    # Basic name sanitization (replace spaces, etc.)
    project_name = project_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    project_dir = cwd / project_name

    ensure_empty_or_confirm(project_dir, force=args.force)
    project_dir.mkdir(exist_ok=True)

    create_structure(project_dir, force=args.force)
    init_git(project_dir, skip_git=args.no_git)
    print_next_steps(project_dir)

if __name__ == "__main__":
    main()
