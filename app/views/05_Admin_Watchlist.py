import streamlit as st
from app.db.utils import (
    init_user_tables,
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    get_holdings,
    update_holding,
    remove_holding,
)
from app.db.connection import get_duckdb_connection


def main():
    st.title("🛡️ Admin: Watchlist & Holdings")
    init_user_tables()

    tab1, tab2 = st.tabs(["📋 Watchlist Manager", "💰 Holdings Manager"])

    with tab1:
        st.header("Watchlist Management")
        with st.form("add_symbol_form"):
            new_sym = st.text_input("Symbol").upper()
            tags = st.text_input("Tags (comma separated)")
            note = st.text_area("Note")
            if st.form_submit_button("Add to Watchlist"):
                if new_sym:
                    add_to_watchlist(new_sym, tags, note)
                    st.success(f"Added {new_sym} to watchlist")
                    st.experimental_rerun()

        watchlist = get_watchlist()
        df = None
        if watchlist:
            df = get_watchlist_dataframe(watchlist)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No watchlist symbols yet. Add one above.")

        if watchlist:
            sym_to_del = st.selectbox("Select symbol to remove", [row["symbol"] for row in watchlist])
            if st.button("🗑️ Remove Symbol", key="remove_watchlist"):
                remove_from_watchlist(sym_to_del)
                st.success(f"Removed {sym_to_del} from watchlist")
                st.experimental_rerun()

    with tab2:
        st.header("Holdings Management")
        with st.form("holding_form"):
            h_sym = st.text_input("Symbol").upper()
            qty = st.number_input("Quantity", min_value=0.0, step=0.1)
            cost = st.number_input("Cost", min_value=0.0, step=0.01)
            if st.form_submit_button("Update Holding"):
                if h_sym:
                    update_holding(h_sym, qty, cost)
                    st.success(f"Saved holding for {h_sym}")
                    st.experimental_rerun()

        holdings = get_holdings()
        if holdings:
            df_h = get_holdings_dataframe(holdings)
            st.dataframe(df_h, use_container_width=True)
            sym_to_del_hold = st.selectbox(
                "Select holding to remove",
                [row["symbol"] for row in holdings],
                key="holding_remove",
            )
            if st.button("Remove Holding", key="remove_holding"):
                remove_holding(sym_to_del_hold)
                st.success(f"Removed holding {sym_to_del_hold}")
                st.experimental_rerun()
        else:
            st.info("No holdings recorded yet. Add positions above.")


def get_watchlist_dataframe(watchlist):
    import pandas as pd

    return pd.DataFrame(watchlist)


def get_holdings_dataframe(holdings):
    import pandas as pd

    return pd.DataFrame(holdings)


if __name__ == "__main__":
    main()
