import streamlit as st
from app.db.utils import (
    init_user_tables,
    get_all_stocks,
    add_or_update_stock,
    remove_stock,
)
from app.db.connection import get_duckdb_connection


def main():
    st.title("🛡️ Admin: Portfolio Manager")
    init_user_tables()

    # Add new stock form
    st.header("➕ Add/Edit Stock")
    with st.form("stock_form"):
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Symbol").upper().strip()
            quantity = st.number_input("Quantity", min_value=0.0, step=0.1, value=0.0)
        with col2:
            avg_cost = st.number_input("Avg Cost (optional)", min_value=0.0, step=0.01, value=0.0)
            tags = st.text_input("Tags (comma separated)")
        note = st.text_area("Note")

        submitted = st.form_submit_button("Save Stock")
        if submitted and symbol:
            add_or_update_stock(symbol, quantity, avg_cost if avg_cost > 0 else None, tags, note)
            st.success(f"Saved {symbol} ({'Holding' if quantity > 0 else 'Watchlist'})")
            st.rerun()

    # Display all stocks
    st.header("📊 All Stocks")
    stocks = get_all_stocks()

    if stocks:
        # Create dataframe for display
        import pandas as pd
        df = pd.DataFrame(stocks)
        df["type"] = df["is_holding"].map({True: "Holding", False: "Watchlist"})
        df = df[["symbol", "type", "quantity", "avg_cost", "tags", "note", "updated_at"]]
        df.columns = ["Symbol", "Type", "Quantity", "Avg Cost", "Tags", "Note", "Updated"]

        st.dataframe(df, use_container_width=True)

        # Quick edit section
        st.header("⚡ Quick Edit")
        if stocks:
            selected_symbol = st.selectbox(
                "Select stock to edit",
                [s["symbol"] for s in stocks],
                key="edit_select"
            )

            selected_stock = next(s for s in stocks if s["symbol"] == selected_symbol)

            with st.form("quick_edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_quantity = st.number_input(
                        "Quantity",
                        min_value=0.0,
                        step=0.1,
                        value=float(selected_stock["quantity"])
                    )
                    new_avg_cost = st.number_input(
                        "Avg Cost",
                        min_value=0.0,
                        step=0.01,
                        value=float(selected_stock["avg_cost"] or 0)
                    )
                with col2:
                    new_tags = st.text_input("Tags", value=selected_stock["tags"])
                    new_note = st.text_area("Note", value=selected_stock["note"])

                if st.form_submit_button("Update Stock"):
                    add_or_update_stock(
                        selected_symbol,
                        new_quantity,
                        new_avg_cost if new_avg_cost > 0 else None,
                        new_tags,
                        new_note
                    )
                    st.success(f"Updated {selected_symbol}")
                    st.rerun()

        # Remove stock
        st.header("🗑️ Remove Stock")
        symbol_to_remove = st.selectbox(
            "Select stock to remove",
            [s["symbol"] for s in stocks],
            key="remove_select"
        )
        if st.button("Remove Stock", key="remove_btn"):
            remove_stock(symbol_to_remove)
            st.success(f"Removed {symbol_to_remove}")
            st.rerun()

    else:
        st.info("No stocks added yet. Add one above.")


if __name__ == "__main__":
    main()
