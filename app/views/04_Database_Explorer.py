import streamlit as st
from sqlalchemy import text

from app.config import get_config
from app.db.connection import get_connection


def main():
    cfg = get_config()
    backend = "Postgres" if cfg.postgres_url else "DuckDB"

    st.title("🗄️ Database Explorer")
    st.markdown(
        f"Use this page to inspect the active database backend: **{backend}**."
    )

    with get_connection() as conn:
        if cfg.postgres_url:
            tables = [row[0] for row in conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public' ORDER BY tablename")).all()]
        else:
            tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]

    st.sidebar.header(f"{backend} Tables")
    if tables:
        st.sidebar.write("\n".join(tables))
    else:
        st.sidebar.info("No tables found yet.")

    selected_table = st.selectbox("Select table to preview", [""] + tables)
    if selected_table:
        with get_connection() as conn:
            if cfg.postgres_url:
                sample_result = conn.execute(text(f"SELECT * FROM {selected_table} LIMIT 100"))
                schema_result = conn.execute(
                    text(
                        "SELECT column_name, data_type, is_nullable "
                        "FROM information_schema.columns "
                        "WHERE table_name = :table_name "
                        "ORDER BY ordinal_position"
                    ),
                    {"table_name": selected_table},
                )
                sample = sample_result.mappings().all()
                schema = schema_result.mappings().all()
            else:
                sample = conn.execute(f"SELECT * FROM {selected_table} LIMIT 100").df()
                schema = conn.execute(f"DESCRIBE {selected_table}").df()

        st.subheader(f"Schema for {selected_table}")
        st.dataframe(schema, use_container_width=True)
        st.subheader(f"Sample rows from {selected_table}")
        st.dataframe(sample, use_container_width=True)

    st.markdown("---")
    st.subheader("Run ad hoc SQL")
    default_sql = "SELECT * FROM watchlist LIMIT 100"
    sql = st.text_area("SQL query", value=default_sql, height=180)
    if st.button("Run query"):
        if not sql.strip():
            st.error("Please enter a SQL query.")
        else:
            try:
                with get_connection() as conn:
                    if cfg.postgres_url:
                        result = conn.execute(text(sql))
                        st.dataframe(result.mappings().all(), use_container_width=True)
                    else:
                        result = conn.execute(sql).df()
                        st.dataframe(result, use_container_width=True)
            except Exception as exc:
                st.error(str(exc))


if __name__ == "__main__":
    main()
