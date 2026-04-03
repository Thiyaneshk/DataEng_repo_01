# Future Platform Roadmap – Data Engineering Growth

This document captures the long‑term path for evolving this project from a local DuckDB playground into a realistic data platform that uses Postgres, Snowflake, Databricks, and LLM/RAG.

The goal is to **learn like a Data Engineer**:
- Start local and simple.
- Add realistic warehouse/orchestration pieces.
- Then move into cloud warehouses and lakehouse platforms.
- Finally add LLM/RAG and cloud deployment.

---

## Phase 0 – Current State (Local Analytics Stack)

**Status: In progress / active**

Technologies already in this repo:

- **Streamlit** for the UI (secure login with Google OAuth, landing page, dashboards).
- **DuckDB** as local analytics DB (5‑minute yfinance prices, daily aggregations).
- **dbt + dbt‑duckdb** for modeling:
  - `stg_prices_5m`
  - `fct_daily_prices` (5m → 1D)
  - `fct_indicators_1d` (EMA, ATR/bands, etc.)
- **Airflow** (DAG scaffold) for scheduled ETL + dbt runs.
- **Developer tools**:
  - `scripts/duckdb_inspect.py` for quick table/schema inspection.
  - `scaffold_v2.py` for project scaffolding.

This phase is about getting a **solid local DE project** that can be run end‑to‑end on the Mac mini.

---

## Phase 1 – Classic Warehouse Tier (Postgres Next to DuckDB)

**Goal:** Learn how to design and run the same models on a “real” warehouse engine, not just an embedded DB.

Planned steps:

1. **Postgres via Docker**
   - Add a Postgres service in `docker-compose`:
     - One **instance/container**.
     - At least two **databases**:
       - `airflow_meta` – for Airflow metadata tables.
       - `analytics` – for future warehouse tables.
   - Document how to bring it up and connect from the app/dbt.

2. **dbt Target: Postgres**
   - Add a `postgres` target in `dbt` `profiles.yml`.
   - Start by:
     - Loading a small subset of price data into `analytics` (e.g., export from DuckDB).
     - Running the same core models (`stg_prices_5m`, `fct_daily_prices`, `fct_indicators_1d`) on Postgres.
   - Keep DuckDB as the primary for now; Postgres is a learning mirror.

3. **Schema Design Practice**
   - Treat `analytics` as a mini warehouse:
     - Separate schemas: `raw`, `staging`, `marts`.
     - Use proper keys, indexes, and constraints.
   - Compare query plans and performance vs DuckDB.

Outcome: Comfort with **dbt on Postgres** and a mental model of how to lift a local analytics schema into a server‑style warehouse.

---

## Phase 2 – Cloud Warehouse Tier A (Snowflake)

**Goal:** Learn how a modern cloud data warehouse works and how to run dbt there.

Planned steps:

1. **Snowflake Trial**
   - Create a Snowflake trial account.
   - Create:
     - A database for this project (e.g., `MARKET_DATA`).
     - A schema layout similar to local: `RAW`, `STAGING`, `MARTS`.
     - A small, cost‑conscious warehouse.

2. **dbt Target: Snowflake**
   - Add a `snowflake` target in `profiles.yml`.
   - Configure:
     - Account, role, warehouse, database, schema.
   - Use dbt to:
     - Load a sample of `raw_prices_5m` (either via dbt seeds, or a simple load script).
     - Run the same models:
       - `stg_prices_5m`
       - `fct_daily_prices`
       - `fct_indicators_1d`

3. **Snowflake Features to Learn**
   - Warehouses, auto‑suspend, and credit usage.
   - Time Travel and cloning (e.g., clone `MARTS` to test changes).
   - Role‑based access control at a simple level.

Outcome: dbt models running on **Snowflake**, understanding of warehouses/costs, and how to map local DuckDB/Postgres thinking into Snowflake’s model.

---

## Phase 3 – Cloud Lakehouse Tier B (Databricks)

**Goal:** Learn the lakehouse / Spark side of data engineering and see the same business logic in Spark/Delta.

Planned steps:

1. **Databricks Free Edition**
   - Create a Databricks Free (Community) account.
   - Set up:
     - A workspace.
     - A cluster suitable for small dev workloads.

2. **Data Landing & Delta Tables**
   - Export a sample of `raw_prices_5m` from local (CSV/Parquet).
   - Land it in Databricks (e.g., DBFS or cloud storage).
   - Create Delta tables:
     - `raw_prices_5m`
     - `daily_prices`
     - `indicators_1d` (if feasible).

3. **Notebooks & Spark SQL**
   - Rebuild:
     - 5m → 1D aggregation in Spark SQL.
     - Basic indicators in Spark (or simple UDFs/UDAFs for RSI/EMA).
   - Optionally:
     - Use Databricks Workflows to orchestrate these steps as a small pipeline.

4. **ML/Feature Engineering**
   - Treat the `indicators_1d`/features table as a feature store seed.
   - Build a simple notebook:
     - Train a toy model (e.g., next‑day return classifier/regressor).
     - Log with MLflow (if desired).

Outcome: Hands‑on experience with the **Databricks lakehouse** approach and Spark‑based DE on the same business problem.

---

## Phase 4 – LLM / RAG Layer

**Goal:** Build a small research assistant on top of the engineered data.

Planned ideas:

1. **Local or API LLM**
   - Start with an API (OpenAI, etc.) or local (Ollama) for:
     - Question‑answering over stock metrics and indicators.
   - Later, move to a Dockerized LLM or dedicated service.

2. **RAG Design**
   - Use existing tables to generate:
     - Per‑symbol, per‑period summaries (e.g., last 30 days).
   - Store these summaries or raw features in a form suitable for retrieval.
   - Build a Streamlit view:
     - Select symbol/date range.
     - Retrieve context from DuckDB/Snowflake/Databricks.
     - Send to LLM with a structured prompt.
     - Display responses with disclaimers (no financial advice).

3. **Cloud Deployment (Later)**
   - Move Streamlit and parts of the pipeline into:
     - AWS (e.g., ECS/Fargate, EKS, or Lambda + API).
     - Or another cloud of choice.
   - Align infra with the chosen warehouse (Snowflake, Databricks on cloud provider).

Outcome: An **LLM‑aware DE project** that shows you can take engineered data and use it in an intelligent assistant pattern.

---

## Phase 5 – Production‑Style Hardening (Optional)

Longer‑term enhancements once the above is stable:

- **Observability**
  - Metrics on ETL runs (row counts, durations, failures).
  - Centralized logging (e.g., ELK, OpenSearch, or a simple structured log table).
- **Data Quality**
  - dbt tests covering:
    - Not‑null/unique constraints on key models.
    - Reasonable ranges for numeric fields.
  - Alerts via Airflow or external tools.
- **Multi‑environment Layout**
  - Dev/test/prod schemas or databases.
  - CI checks on dbt models and basic tests.

---

## Guiding Principle

At every stage, reuse the **same business problem**:

> Multi‑timeframe equity price data with daily aggregations and technical indicators.

Only change the **platform** (DuckDB → Postgres → Snowflake → Databricks) and the way you orchestrate and serve it.

This keeps cognitive load manageable while showing real progression on your data engineering path.
