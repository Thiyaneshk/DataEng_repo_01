# de_template

Phase 0 template for:
- Streamlit + uv
- DuckDB first, later Postgres
- CLI (scripts/refresh_data.py) + UI (app/main.py)
- dbt skeleton (dbt/)
- Airflow skeleton (airflow/)

## Learning checkpoints

1. Set up environment:
   - `uv sync`

2. Run the CLI:
   - `uv run python -m scripts.refresh_data`

3. Run the UI:
   - `uv run streamlit run app/main.py`

4. Add Google OAuth in `app/auth.py`.

5. Add Postgres support in `app/db/connection.py`.

6. Initialize dbt inside `dbt/` and point it at DuckDB/Postgres.

7. Add an Airflow DAG in `airflow/dags/` that calls your ETL logic.
