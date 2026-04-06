import streamlit as st

from app.config import get_config
from app.db.connection import get_connection


def main():
    cfg = get_config()
    backend = "Postgres" if cfg.postgres_url else "DuckDB"

    st.title("⚙️ Admin: Platform Setup & Ops")
    st.write("This page provides instructions and tools for managing your Mac mini M4 platform.")

    tab1, tab2, tab3 = st.tabs(["🚀 Docker & Airflow", "🛠️ Mac mini M4 Tuning", "🧹 Database Maintenance"])

    with tab1:
        st.header("Docker & Airflow Setup")
        st.info("Follow these steps to launch your orchestration layer on Mac mini M4.")

        st.markdown("""
        ### 1. Prerequisites
        - Install **Docker Desktop for Mac** (Apple Silicon version).
        - Ensure Docker is running.

        ### 2. Launching the Stack
        Open your terminal in the project root and run:
        ```bash
        # Start Airflow and Postgres
        docker-compose up -d
        ```

        ### 3. Accessing Airflow
        - **URL**: [http://localhost:8080](http://localhost:8080)
        - **Default Username**: `admin`
        - **Default Password**: `admin`

        ### 4. Stopping the Stack
        ```bash
        docker-compose down
        ```
        """)

    with tab2:
        st.header("Mac mini M4 Optimization")
        st.markdown("""
        ### Resource Allocation
        - **Unified Memory**: M4 is excellent for LLMs. Ensure Docker has at least 8GB allocated if running Airflow + Local LLMs.
        - **Metal acceleration**: Ollama automatically uses the M4 GPU.
        """)

    with tab3:
        st.header("DB Operations")
        st.write(f"**Active backend:** {backend}")
        if cfg.postgres_url:
            st.write(f"**Postgres URL:** `{cfg.postgres_url}`")
            st.write("You can connect from your host using `localhost:5432`.")
        else:
            st.write("This app is currently using DuckDB. Set `POSTGRES_URL` to switch to Postgres.")

        if st.button("🔍 Check DB Connection"):
            try:
                with get_connection() as conn:
                    if cfg.postgres_url:
                        version = conn.exec_driver_sql("SELECT version()").fetchone()[0]
                    else:
                        version = conn.execute("SELECT version()").fetchone()[0]
                    st.success(f"Connected! {backend} Version: {version}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

if __name__ == "__main__":
    main()
