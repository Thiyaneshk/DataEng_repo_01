from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from app.core.etl.prices import load_prices


def run_dbt_postgres():
    import subprocess
    subprocess.run(
        ["dbt", "run", "--profiles-dir", "/app/dbt", "--target", "postgres"],
        check=True,
        cwd="/app/dbt",
    )


def load_prices_task():
    load_prices()


with DAG(
    dag_id="etl_prices_and_dbt",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Refresh prices in DuckDB and run dbt (Postgres)",
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
) as dag:

    load_prices_op = PythonOperator(
        task_id="load_prices_duckdb",
        python_callable=load_prices_task,
    )

    dbt_run_op = PythonOperator(
        task_id="run_dbt_postgres",
        python_callable=run_dbt_postgres,
    )

    load_prices_op >> dbt_run_op
