import streamlit as st
from app.db.connection import get_duckdb_connection


def main():
    st.title("🗄️ Database Explorer")
    st.markdown(
        "Use this page to inspect DuckDB tables, preview data, and run ad hoc SQL queries."
    )

    with get_duckdb_connection() as conn:
        tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]

    st.sidebar.header("DuckDB Tables")
    if tables:
        st.sidebar.write("\n".join(tables))
    else:
        st.sidebar.info("No DuckDB tables found yet.")

    selected_table = st.selectbox("Select table to preview", [""] + tables)
    if selected_table:
        with get_duckdb_connection() as conn:
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
                with get_duckdb_connection() as conn:
                    result = conn.execute(sql).df()
                st.dataframe(result, use_container_width=True)
            except Exception as exc:
                st.error(str(exc))

if __name__ == "__main__":
    main()
