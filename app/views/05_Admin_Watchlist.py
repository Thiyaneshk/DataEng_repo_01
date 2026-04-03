import streamlit as st
from app.db.utils import init_user_tables, get_watchlist_symbols, add_to_watchlist, remove_from_watchlist, update_holding
from app.db.connection import get_duckdb_connection

def main():
    st.title("🛡️ Admin: Watchlist & Holdings")
    init_user_tables()

    tab1, tab2 = st.tabs(["📋 Watchlist Manager", "💰 Holdings Manager"])

    with tab1:
        st.header("Watchlist Management")
        with st.form("add_symbol_form"):
            new_sym = st.text_input("Symbol").upper()
            if st.form_submit_button("Add to Watchlist"):
                if new_sym:
                    add_to_watchlist(new_sym)
                    st.success(f"Added {new_sym}")
                    st.rerun()

        with get_duckdb_connection() as conn:
            df = conn.execute("SELECT * FROM watchlist").df()
        st.dataframe(df, use_container_width=True)

        sym_to_del = st.selectbox("Select symbol to remove", df['symbol'] if not df.empty else [])
        if st.button("🗑️ Remove Symbol"):
            remove_from_watchlist(sym_to_del)
            st.rerun()

    with tab2:
        st.header("Holdings Management")
        with st.form("holding_form"):
            h_sym = st.text_input("Symbol").upper()
            qty = st.number_input("Quantity", min_value=0.0)
            cost = st.number_input("Cost")
            if st.form_submit_button("Update Holding"):
                update_holding(h_sym, qty, cost)
                st.rerun()

        with get_duckdb_connection() as conn:
            df_h = conn.execute("SELECT * FROM holdings").df()
        st.dataframe(df_h, use_container_width=True)

if __name__ == "__main__":
    main()
