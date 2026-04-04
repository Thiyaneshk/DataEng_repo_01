from datetime import datetime, timedelta
import subprocess
import sys
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


def load_prices_task():
    """Load latest prices from yfinance into DuckDB"""
    import sys
    import os
    # When running in Airflow, /app is the root of project
    # So add /app to path to make 'app' module importable
    # /app/app is the actual app package
    sys.path.insert(0, os.path.dirname("/app"))  # This makes it /
    
    try:
        from app.core.etl.prices import load_prices_5m
        count = load_prices_5m(period="5d")
        print(f"✅ Loaded {count} price records into DuckDB")
        return count
    except Exception as e:
        print(f"❌ Price loading failed: {str(e)}")
        raise


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

    dbt_run_op = BashOperator(
        task_id="run_dbt_postgres",
        bash_command="cd /app/dbt && dbt run --profiles-dir /app/dbt --target postgres",
    )

    load_prices_op >> dbt_run_op
