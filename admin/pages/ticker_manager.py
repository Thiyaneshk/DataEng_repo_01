"""
Ticker Manager Page (02_Ticker_Manager.py)
Add, edit, delete stocks from watchlist and holdings.
"""

import streamlit as st
from app.db.utils import get_all_stocks, add_or_update_stock, remove_stock
import pandas as pd


def show():
    """Render ticker manager page."""
    
    st.title("📝 Ticker Manager")
    st.markdown("Manage watchlist and holdings")
    st.markdown("---")
    
    # Tabs for different actions
    tab1, tab2, tab3 = st.tabs(["View All", "Add New", "Delete"])
    
    # TAB 1: View All Stocks
    with tab1:
        st.markdown("### All Tickers")
        
        try:
            stocks = get_all_stocks()
            
            if stocks:
                # Separate watchlist and holdings
                df_data = []
                for stock in stocks:
                    symbol, quantity, avg_cost, tags, note, created_at = stock
                    df_data.append({
                        "Symbol": symbol,
                        "Quantity": quantity,
                        "Avg Cost": f"${avg_cost:.2f}" if avg_cost else "N/A",
                        "Tags": tags if tags else "-",
                        "Note": note if note else "-",
                        "Type": "Holding" if quantity > 0 else "Watchlist"
                    })
                
                df = pd.DataFrame(df_data)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Holdings", len([s for s in df_data if s['Type'] == 'Holding']))
                with col2:
                    st.metric("Total Watchlist", len([s for s in df_data if s['Type'] == 'Watchlist']))
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No tickers yet. Add one to get started!")
        
        except Exception as e:
            st.error(f"Failed to load stocks: {e}")
    
    # TAB 2: Add New
    with tab2:
        st.markdown("### Add New Ticker")
        
        with st.form("add_ticker_form"):
            symbol = st.text_input("Stock Symbol", placeholder="e.g., AAPL").upper()
            quantity = st.number_input("Quantity", min_value=0, value=0, step=1)
            avg_cost = st.number_input("Average Cost ($)", min_value=0.0, step=0.01)
            tags = st.text_input("Tags (comma-separated)", placeholder="tech, usa, large-cap")
            note = st.text_area("Notes", placeholder="Optional: investment thesis, buying opportunity, etc.")
            
            submitted = st.form_submit_button("➕ Add Ticker", use_container_width=True)
        
        if submitted:
            if not symbol or len(symbol) < 1:
                st.error("❌ Please enter a symbol")
            else:
                with st.spinner(f"Adding {symbol}..."):
                    try:
                        add_or_update_stock(symbol, quantity, avg_cost, tags, note)
                        st.success(f"✓ {symbol} added!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Failed to add {symbol}: {e}")
    
    # TAB 3: Delete
    with tab3:
        st.markdown("### Delete Ticker")
        st.warning("⚠️ This action cannot be undone!")
        
        try:
            stocks = get_all_stocks()
            symbols = [s[0] for s in stocks]
            
            if symbols:
                symbol_to_delete = st.selectbox("Select ticker to delete", symbols)
                
                if st.button("🗑️ Delete", use_container_width=True):
                    confirm = st.checkbox(f"Confirm: I want to delete {symbol_to_delete}")
                    
                    if confirm:
                        with st.spinner(f"Deleting {symbol_to_delete}..."):
                            try:
                                remove_stock(symbol_to_delete)
                                st.success(f"✓ {symbol_to_delete} deleted!")
                            except Exception as e:
                                st.error(f"Failed to delete: {e}")
            else:
                st.info("No tickers to delete")
        
        except Exception as e:
            st.error(f"Failed to load stocks: {e}")
