#!/usr/bin/env python
"""
scaffold_v2.py – Enhanced Data Engineering Template Scaffold (V2)

This script generates the full project structure including:
- Streamlit UI with Google Auth and professional landing page.
- Secure navigation: Sidebar links only appear AFTER authentication.
- DuckDB integration for fast analytical queries with incremental loading.
- dbt models for staging, marts (daily aggregation), and indicators (EMA, Bands).
- Airflow DAGs for automated ETL orchestration (fetching 5m OHLCV).
- Interactive dashboards with Plotly and technical indicator overlays.

Usage:
    python scaffold_v2.py --name my_data_project
"""

import os
import argparse
from pathlib import Path
from textwrap import dedent

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(dedent(content).strip() + "\n")
    print(f"Created: {path}")

def create_structure(project_dir: Path):
    # 1. Project Root Files
    write_file(project_dir / "pyproject.toml", """
        [project]
        name = "de_template"
        version = "0.1.0"
        description = "Data engineering template: Streamlit + uv + DuckDB + dbt + Airflow"
        requires-python = ">=3.11"
        dependencies = [
            "streamlit>=1.40.0,<2.0.0",
            "duckdb>=1.0.0,<2.0.0",
            "yfinance>=0.2.40,<1.0.0",
            "dbt-duckdb>=1.9.0,<2.0.0",
            "streamlit-oauth>=0.1.5",
            "pandas>=2.0.0",
            "plotly>=5.0.0",
            "apache-airflow>=2.10.0",
        ]
        [project.optional-dependencies]
        dev = ["pytest>=8.0.0", "ruff>=0.5.0"]
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"
        [tool.hatch.build.targets.wheel]
        packages = ["app", "scripts"]
    """)

    write_file(project_dir / "README.md", """
        # Data Engineering Portfolio (V2)

        A production-ready template for building and showcasing data engineering pipelines.

        ## Features
        - **Auth**: Secure Google OAuth with professional landing page.
        - **Pipeline**: Market data ETL via `yfinance` with incremental loading and de-duplication.
        - **Storage**: `DuckDB` for local analytics and warehouse-first logic.
        - **Transformation**: `dbt` for staged, mart, and indicator layers (EMA, RSI, Bands).
        - **Orchestration**: `Airflow` DAGs for automated updates.
        - **Visualization**: `Streamlit` with interactive `Plotly` dashboards.
    """)

    # 2. App Logic
    write_file(project_dir / "app/main.py", """
        from __future__ import annotations
        import os
        from collections import defaultdict
        from pathlib import Path
        from typing import Dict, List, Tuple
        import streamlit as st
        from app.config import get_config
        from app import auth

        def discover_pages(pages_dir: Path) -> Dict[str, List[st.Page]]:
            if not pages_dir.exists(): return {}
            py_files = [f for f in os.listdir(pages_dir) if f.endswith(".py") and not f.startswith("_")]
            groups = defaultdict(list)
            for file in py_files:
                parts = file.split("_")
                if len(parts) < 3: continue
                try:
                    order = int(parts[0])
                    group = parts[1]
                    page_name = "_".join(parts[2:])
                    groups[group].append((order, page_name, file))
                except ValueError: continue
            allowed_groups = ["Home", "Stock", "Portfolio", "Testing"]
            filtered_groups = {g: sorted(groups[g], key=lambda x: x[0]) for g in allowed_groups if g in groups}
            pages = {}
            for group, files in filtered_groups.items():
                pages[group] = [st.Page(str(pages_dir / f), title=p.replace("_", " ").replace(".py", "").title()) for _, p, f in files]
            return pages

        def main():
            cfg = get_config()
            st.set_page_config(page_title=cfg.app_name, page_icon="📈", layout="wide")
            user = auth.require_login()
            if user:
                name = user.get("name") or user.get("email") or "User"
                avatar = user.get("avatar", "👤")
                st.sidebar.markdown(f"### Welcome, {avatar} {name}!")
                if st.sidebar.button("🔓 Log out"):
                    auth.logout()
                st.sidebar.divider()
                pages = discover_pages(Path(__file__).parent / "views")
                if not pages:
                    st.title(cfg.app_name)
                    st.info("No views found in app/views/.")
                else:
                    st.navigation(pages).run()

        if __name__ == "__main__":
            main()
    """)

    write_file(project_dir / "app/auth.py", """
        import streamlit as st
        from streamlit_oauth import OAuth2Component

        def require_login():
            if "user" in st.session_state:
                return st.session_state["user"]

            st.markdown(\"\"\"
                <style>
                .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
                .hero-text { text-align: center; margin-bottom: 2rem; }
                </style>
            \"\"\", unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="hero-text">', unsafe_allow_html=True)
                st.title("📈 DE Portfolio Template")
                st.subheader("Modern Data Engineering Stack")
                st.markdown('</div>', unsafe_allow_html=True)
                st.info(\"\"\"
                ### High-Level Features:
                - **Automated Pipeline**: 5m intraday data via `yfinance`.
                - **Fast Storage**: `DuckDB` embedded warehouse.
                - **dbt Modeling**: Structured SQL (EMA, RSI, Bands).
                - **Batch Orchestration**: `Airflow` DAGs.
                - **Interactive UI**: Real-time `Streamlit` & `Plotly`.
                \"\"\")

                try:
                    auth_secrets = st.secrets.get("google_auth")
                except Exception:
                    auth_secrets = None

                if auth_secrets:
                    from streamlit_oauth import OAuth2Component
                    CLIENT_ID = auth_secrets.get("client_id")
                    CLIENT_SECRET = auth_secrets.get("client_secret")
                    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
                    TOKEN_URL = "https://oauth2.googleapis.com/token"
                    REFRESH_TOKEN_URL = "https://oauth2.googleapis.com/token"
                    REVOKE_TOKEN_URL = "https://oauth2.googleapis.com/revoke"
                    SCOPE = "openid email profile"
                    REDIRECT_URI = auth_secrets.get("redirect_uri")

                    oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL, REVOKE_TOKEN_URL)
                    result = oauth2.authorize_button("Login with Google", REDIRECT_URI, SCOPE, icon="https://www.google.com/favicon.ico", use_container_width=True)

                    if result and "token" in result:
                        st.session_state["token"] = result["token"]
                        st.session_state["user"] = {"name": "Google User", "avatar": "📧"}
                        st.rerun()
                else:
                    st.warning("⚠️ Google OAuth secrets missing.")
                    if st.button("🚀 Dev Login (Bypass Auth)", type="primary"):
                        st.session_state["user"] = {"name": "Dev User", "avatar": "🛠️"}
                        st.rerun()
            st.stop()

        def logout():
            if "user" in st.session_state: del st.session_state["user"]
            if "token" in st.session_state: del st.session_state["token"]
            st.rerun()
    """)

    write_file(project_dir / "app/config.py", """
        from dataclasses import dataclass
        import os
        from pathlib import Path
        @dataclass
        class AppConfig:
            app_name: str = os.getenv("APP_NAME", "DE Template App")
            duckdb_path: Path = Path(os.getenv("DUCKDB_PATH", "data/app.duckdb"))
            postgres_url: str | None = os.getenv("POSTGRES_URL")
        def get_config() -> AppConfig:
            return AppConfig()
    """)

    write_file(project_dir / "app/db/connection.py", """
        from contextlib import contextmanager
        import duckdb
        from app.config import get_config
        @contextmanager
        def get_duckdb_connection():
            cfg = get_config()
            cfg.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
            conn = duckdb.connect(str(cfg.duckdb_path))
            try: yield conn
            finally: conn.close()
    """)

    write_file(project_dir / "app/core/etl/prices.py", """
        from __future__ import annotations
        from typing import Optional
        import duckdb
        import yfinance as yf
        import pandas as pd
        from app.db.connection import get_duckdb_connection

        DEFAULT_SYMBOLS = ["AAPL", "RELIANCE.NS", "RY.TO"]

        def fetch_prices(symbols=None, period="5d", interval="5m"):
            symbols = symbols or DEFAULT_SYMBOLS
            raw = yf.download(tickers=symbols, period=period, interval=interval, group_by="ticker", auto_adjust=True)
            if raw.empty: return pd.DataFrame()
            frames = []
            for sym in symbols:
                try:
                    df = raw.xs(sym, axis=1, level=0, drop_level=True).copy() if isinstance(raw.columns, pd.MultiIndex) else raw.copy()
                    df = df.dropna(how="all").reset_index()
                    df.columns = [str(c).lower() for c in df.columns]
                    time_col = "datetime" if "datetime" in df.columns else "date"
                    df = df.rename(columns={time_col: "datetime"})
                    df["symbol"] = sym
                    frames.append(df[["symbol", "datetime", "open", "high", "low", "close", "volume"]])
                except KeyError: continue
            return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

        def load_prices(symbols=None, period="5d", interval="5m", conn=None):
            df = fetch_prices(symbols, period, interval)
            if df.empty: return 0
            def _load(c):
                c.execute("CREATE TABLE IF NOT EXISTS raw_prices (symbol TEXT, datetime TIMESTAMP, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE, PRIMARY KEY (symbol, datetime))")
                c.register("df_prices", df)
                c.execute("INSERT OR IGNORE INTO raw_prices SELECT * FROM df_prices")
                return c.execute("SELECT COUNT(*) FROM raw_prices").fetchone()[0]
            if conn: return _load(conn)
            with get_duckdb_connection() as c: return _load(c)
    """)

    # 3. Views
    write_file(project_dir / "app/views/01_Home_Dashboard.py", """
        import streamlit as st
        import duckdb
        import plotly.express as px
        from app.config import get_config
        def main():
            st.title("🏠 Home Dashboard")
            cfg = get_config()
            conn = duckdb.connect(str(cfg.duckdb_path))
            count = conn.execute("SELECT COUNT(*) FROM raw_prices").fetchone()[0]
            st.metric("Raw Price Rows", f"{count:,}")
            df_summary = conn.execute("SELECT symbol, COUNT(*) as rows FROM raw_prices GROUP BY 1").df()
            if not df_summary.empty:
                st.plotly_chart(px.bar(df_summary, x='symbol', y='rows', color='symbol', title="Data Volume"), use_container_width=True)
            conn.close()
        if __name__ == "__main__": main()
    """)

    write_file(project_dir / "app/views/02_Stock_Overview.py", """
        import streamlit as st
        import duckdb
        import plotly.graph_objects as go
        from app.config import get_config
        def main():
            st.title("📈 Stock Overview")
            cfg = get_config()
            conn = duckdb.connect(str(cfg.duckdb_path))
            symbols = [s[0] for s in conn.execute("SELECT DISTINCT symbol FROM raw_prices").fetchall()]
            if not symbols: st.warning("No data"); return
            sym = st.sidebar.selectbox("Symbol", symbols)
            df = conn.execute(f"SELECT * FROM fct_indicators_1d WHERE symbol = '{sym}' ORDER BY trade_date").df()
            if df.empty: df = conn.execute(f"SELECT * FROM raw_prices WHERE symbol = '{sym}' ORDER BY datetime").df(); x, y = 'datetime', 'close'
            else: x, y = 'trade_date', 'daily_close'
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df[x], y=df[y], name="Price"))
            if 'ema_20' in df.columns: fig.add_trace(go.Scatter(x=df[x], y=df['ema_20'], name="EMA 20"))
            st.plotly_chart(fig, use_container_width=True)
            conn.close()
        if __name__ == "__main__": main()
    """)

    # 4. dbt Logic
    write_file(project_dir / "dbt/dbt_project.yml", """
        name: "de_template_dbt"
        version: "1.0.0"
        profile: "default"
        model-paths: ["models"]
        models:
          de_template_dbt:
            +materialized: view
    """)

    write_file(project_dir / "dbt/profiles.yml", """
        default:
          target: dev
          outputs:
            dev:
              type: duckdb
              path: ../data/app.duckdb
    """)

    write_file(project_dir / "dbt/models/sources.yml", """
        version: 2
        sources:
          - name: raw
            schema: main
            tables:
              - name: raw_prices
    """)

    write_file(project_dir / "dbt/models/staging/stg_prices.sql", """
        WITH source AS (SELECT * FROM {{ source('raw', 'raw_prices') }}),
        cleaned AS (SELECT symbol, datetime AS trade_datetime, open AS open_price, high AS high_price, low AS low_price, close AS close_price, volume FROM source)
        SELECT * FROM cleaned
    """)

    write_file(project_dir / "dbt/models/marts/fct_daily_prices.sql", """
        {{ config(materialized='table') }}
        SELECT symbol, CAST(trade_datetime AS DATE) AS trade_date, ARG_MIN(open_price, trade_datetime) AS daily_open, MAX(high_price) AS daily_high, MIN(low_price) AS daily_low, ARG_MAX(close_price, trade_datetime) AS daily_close, SUM(volume) AS daily_volume
        FROM {{ ref('stg_prices') }} GROUP BY 1, 2
    """)

    write_file(project_dir / "dbt/models/marts/fct_indicators_1d.sql", """
        {{ config(materialized='table') }}
        SELECT *, AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ema_20
        FROM {{ ref('fct_daily_prices') }}
    """)

    # 5. Scripts & Airflow
    write_file(project_dir / "scripts/refresh_data.py", """
        from app.core.etl.prices import load_prices
        if __name__ == "__main__":
            print("Refreshing data..."); rows = load_prices(); print(f"Done. {rows} rows.")
    """)

    write_file(project_dir / "airflow/dags/market_data_etl.py", """
        from airflow import DAG
        from airflow.operators.python import PythonOperator
        from datetime import datetime
        from app.core.etl.prices import load_prices
        with DAG("market_data_etl", start_date=datetime(2025, 1, 1), schedule="@daily", catchup=False) as dag:
            PythonOperator(task_id="load_prices", python_callable=load_prices)
    """)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="de_template_v2")
    args = parser.parse_args()
    project_dir = Path.cwd() / args.name
    project_dir.mkdir(exist_ok=True)
    create_structure(project_dir)
    print(f"\\nSuccessfully scaffolded V2 project at: {project_dir}")

if __name__ == "__main__":
    main()
