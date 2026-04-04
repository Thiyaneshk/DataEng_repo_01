"""
Main Streamlit entry point for de_template.

Learning goals:
- Use a central main.py to handle auth + navigation.
- Discover and load sub-pages from the app/pages/ directory.
- Keep business logic out of the UI layer.
"""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st

from app.config import get_config
from app import auth


def discover_pages(pages_dir: Path) -> Dict[str, List[st.Page]]:
    """
    Discover Streamlit pages in the given directory using a naming convention.

    Expected file name pattern (similar to your previous project):
        01_Home_dashboard.py
        02_Stock_overview.py
        03_Portfolio_positions.py
        etc.

    Pattern:
        {order}_{Group}_{page_name}.py

    Where:
        - order: integer used for ordering within a group
        - Group: one of the allowed group names (e.g. Home, Stock, Portfolio, Testing)
        - page_name: remaining part of the filename; underscores become spaces in the UI
    """
    if not pages_dir.exists():
        return {}

    py_files = [
        f
        for f in os.listdir(pages_dir)
        if f.endswith(".py") and not f.startswith("_")
    ]

    groups: Dict[str, List[Tuple[int, str, str]]] = defaultdict(list)

    for file in py_files:
        if "_" not in file:
            continue
        parts = file.split("_")
        if len(parts) < 3:
            continue

        try:
            order = int(parts[0])
        except ValueError:
            # First part is not an integer; skip this file
            continue

        group = parts[1]
        page_name = "_".join(parts[2:])

        groups[group].append((order, page_name, file))

    allowed_groups = ["Home", "Stock", "Portfolio", "Admin", "Analysis", "AI", "Testing"]
    filtered_groups = {
        group: groups[group] for group in allowed_groups if group in groups
    }

    for group in filtered_groups:
        filtered_groups[group].sort(key=lambda x: x[0])

    pages: Dict[str, List[st.Page]] = {}

    for group, files in filtered_groups.items():
        pages[group] = []
        for _, page_name, file in files:
            title = (
                page_name.replace("_", " ")
                .replace(".py", "")
                .title()
            )
            file_path = str(pages_dir / file)
            pages[group].append(st.Page(file_path, title=title))

    return pages


def main() -> None:
    cfg = get_config()

    st.set_page_config(
        page_title=cfg.app_name,
        page_icon="📈",
        layout="wide",
    )

    # --- Auth ---
    user = auth.require_login()  # currently stops and warns until you implement real auth

    # Sidebar header if user info is available
    if user:
        name = user.get("name") or user.get("email") or "User"
        st.sidebar.markdown(f"### Welcome, {name}!")
        if st.sidebar.button("Log out"):
            auth.logout()
        st.sidebar.divider()

    # --- Navigation setup ---
    project_root = Path(__file__).parent  # de_template/app
    pages_dir = project_root / "views"

    pages = discover_pages(pages_dir)

    if not pages:
        # Default dashboard if no pages are discovered
        st.title(cfg.app_name)
        st.info("No pages found in the app/pages directory.")
        st.markdown(
            """
            ### Current Template Features

            - **Config-driven**: Centralized config in `app/config.py`.
            - **DuckDB-first**: Embedded analytics DB via `app/db/connection.py`.
            - **ETL Hooks**: Placeholder ETL in `app/core/etl/prices.py`.
            - **Auth Hook**: `app/auth.py` ready for Google OAuth wiring.
            - **dbt & Airflow Skeletons**: `dbt/` and `airflow/` directories for analytics & orchestration.
            """
        )
        st.success("Template is running. Next: add pages under `app/pages/`.")
        return

    # Run navigation (Streamlit multipage API)
    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    # Recommended runs:
    #   uv run streamlit run app/main.py
    # or:
    #   streamlit run app/main.py
    main()
