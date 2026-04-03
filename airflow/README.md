# Airflow skeleton

Learning goals:
- Run Airflow via docker-compose and add DAGs that orchestrate:
  - Your ETL scripts (scripts/refresh_data.py)
  - dbt runs (dbt/)

Suggested next steps:
- Use the official Airflow docker-compose example.
- Mount this repository into the Airflow webserver/scheduler containers.
- Add a DAG in airflow/dags/ that calls your Python ETL and dbt.
