"""
Holdings Manager Page (03_Holdings_Manager.py)
Edit quantities and costs for existing holdings.
"""

import streamlit as st
from app.db.utils import get_holdings, add_or_update_stock
import pandas as pd


def show():
    """Render holdings manager page."""
    
    st.title("💰 Holdings Manager")
    st.markdown("Update quantities and costs for your positions")
    st.markdown("---")
    
    try:
        holdings = get_holdings()
        
        if not holdings:
            st.info("No holdings yet. Use Ticker Manager to add some!")
            return
        
        # Display current holdings
        st.markdown("### Current Holdings")
        
        df_data = []
        for symbol, quantity, avg_cost, tags, note, created_at in holdings:
            df_data.append({
                "Symbol": symbol,
                "Quantity": quantity,
                "Avg Cost": f"${avg_cost:.2f}" if avg_cost else "N/A",
                "Total Value": f"${quantity * avg_cost:.2f}" if avg_cost else "N/A",
                "Tags": tags if tags else "-"
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            total_value = sum([h[1] * h[2] if h[2] else 0 for h in holdings])
            st.metric("Total Portfolio Value", f"${total_value:.2f}")
        
        st.markdown("---")
        
        # Update Holdings
        st.markdown("### Update Holding")
        
        with st.form("update_holding_form"):
            symbol = st.selectbox("Select Symbol", [h[0] for h in holdings])
            
            # Get current values
            current = next((h for h in holdings if h[0] == symbol), None)
            current_qty = current[1] if current else 0
            current_cost = current[2] if current else 0.0
            
            new_quantity = st.number_input(
                "New Quantity",
                min_value=0,
                value=int(current_qty) if current_qty else 0,
                step=1
            )
            
            new_cost = st.number_input(
                "New Average Cost ($)",
                min_value=0.0,
                value=float(current_cost) if current_cost else 0.0,
                step=0.01
            )
            
            submitted = st.form_submit_button("✏️ Update", use_container_width=True)
        
        if submitted:
            with st.spinner(f"Updating {symbol}..."):
                try:
                    add_or_update_stock(symbol, new_quantity, new_cost)
                    st.success(f"✓ {symbol} updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")
    
    except Exception as e:
        st.error(f"Failed to load holdings: {e}")
