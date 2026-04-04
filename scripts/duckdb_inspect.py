from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_config
from app.db.connection import get_duckdb_connection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the local DuckDB database.")
    parser.add_argument(
        "--table",
        help="Show schema and sample rows for a specific table.",
        default=None,
    )
    parser.add_argument(
        "--limit",
        help="Number of sample rows to display.",
        type=int,
        default=20,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = get_config()

    with get_duckdb_connection() as conn:
        if args.table:
            print(f"Inspecting table: {args.table}\n")
            schema = conn.execute(f"DESCRIBE {args.table}").fetchall()
            print("Schema:")
            for row in schema:
                print("\t".join(str(item) for item in row))
            print("\nSample rows:")
            rows = conn.execute(f"SELECT * FROM {args.table} LIMIT {args.limit}").fetchall()
            for row in rows:
                print(row)
        else:
            tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
            print("Available tables:")
            for table in tables:
                print(f"- {table}")
            print("\nRun with --table TABLE to inspect a specific table.")

if __name__ == "__main__":
    main()
