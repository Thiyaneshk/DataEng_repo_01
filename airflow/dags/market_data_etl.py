from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def etl_task():
    from app.core.etl.prices import load_prices_5m
    from app.db.utils import init_user_tables
    init_user_tables()
    rows = load_prices_5m(period="5d")
    print(f"Loaded {rows} rows")

with DAG("market_data_etl", start_date=datetime(2025, 1, 1), schedule="@daily", catchup=False) as dag:
    PythonOperator(task_id="fetch_and_load", python_callable=etl_task)
